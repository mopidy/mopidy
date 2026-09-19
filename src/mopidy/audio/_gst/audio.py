from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast, override

import pykka

from mopidy import exceptions
from mopidy._lib import logs, process
from mopidy._lib.gi import GLib, Gst, GstBase, GstPbutils
from mopidy.audio import tags as tags_lib
from mopidy.audio._api import Audio
from mopidy.audio._gst.mixer import GstSoftwareMixerAdapter
from mopidy.audio._gst.pipeline import GstPipeline
from mopidy.audio._gst.types import (
    GstAsyncDone,
    GstBuffering,
    GstBusMessage,
    GstEndOfStream,
    GstError,
    GstMissingPlugin,
    GstStateChanged,
    GstStreamStart,
    GstTag,
    GstWarning,
)
from mopidy.audio._listener import AudioListener
from mopidy.audio._utils import setup_proxy
from mopidy.types import DurationMs, PlaybackState

if TYPE_CHECKING:
    from mopidy._exts.softwaremixer.mixer import SoftwareMixerProxy
    from mopidy.config import Config
    from mopidy.mixer import MixerProxy

logger = logging.getLogger(__name__)

# This logger is only meant for debug logging of low level GStreamer info such
# as callbacks, event, messages and direct interaction with GStreamer such as
# set_state() on a pipeline.
gst_logger = logging.getLogger("mopidy.audio.gst")

_GST_STATE_MAPPING: dict[Gst.State, PlaybackState] = {
    Gst.State.PLAYING: PlaybackState.PLAYING,
    Gst.State.PAUSED: PlaybackState.PAUSED,
    Gst.State.NULL: PlaybackState.STOPPED,
}


# TODO: create a player class which replaces the actors internals
class GstAudio(Audio, pykka.ThreadingActor):
    """Audio output through [GStreamer](https://gstreamer.freedesktop.org/)."""

    mixer: GstSoftwareMixerAdapter | None = None

    def __init__(
        self,
        config: Config,
        mixer: MixerProxy | None,
    ) -> None:
        super().__init__()

        self._config = config
        self._target_state: Gst.State = Gst.State.NULL
        self._buffering: bool = False
        self._live_stream: bool = False
        self._tags: dict[str, list[Any]] = {}
        self._pending_uri: str | None = None
        self._pending_tags: dict[str, list[Any]] | None = None

        self._pipeline: GstPipeline | None = None
        self._about_to_finish_callback: Callable | None = None
        self._source_setup_callback: Callable | None = None

        if mixer and self._config["audio"]["mixer"] == "software":
            mixer = cast("SoftwareMixerProxy", mixer)
            self.mixer = pykka.traversable(GstSoftwareMixerAdapter(mixer))

    @override
    def on_start(self) -> None:
        self._thread = threading.current_thread()
        try:
            self._setup_preferences()
            self._pipeline = GstPipeline(
                self._config,
                on_bus_message=self._on_gst_bus_message,
                on_position=self._on_gst_position,
                on_about_to_finish=self._on_gst_about_to_finish,
                on_source_setup=self._on_gst_source_setup,
            )
            if self.mixer:
                self.mixer.setup(self._pipeline.volume, self.actor_ref.proxy().mixer)
        except (GLib.Error, exceptions.AudioException):
            logger.exception("Failed to set up the audio pipeline.")
            process.exit_process()

    @override
    def on_stop(self) -> None:
        self._teardown_mixer()
        if self._pipeline is not None:
            self._pipeline.teardown()

    def _setup_preferences(self) -> None:
        # TODO: move out of audio actor?
        # Fix for https://github.com/mopidy/mopidy/issues/604
        registry = Gst.Registry.get()
        jacksink = registry.find_feature("jackaudiosink", Gst.ElementFactory)
        if jacksink:
            jacksink.set_rank(Gst.Rank.SECONDARY)

    def _teardown_mixer(self) -> None:
        if self.mixer:
            self.mixer.teardown()

    def _on_gst_about_to_finish(self, _element: Gst.Element) -> None:
        if self._thread == threading.current_thread():
            logger.error("about-to-finish in actor, aborting to avoid deadlock.")
            return

        gst_logger.debug("Got about-to-finish event.")
        if self._about_to_finish_callback:
            logger.debug("Running about-to-finish callback.")
            self._about_to_finish_callback()

    def _on_gst_source_setup(
        self,
        _element: Gst.Element,
        source: Gst.Element,
    ) -> None:
        gst_logger.debug(
            "Got source-setup signal: element=%s",
            source.__class__.__name__,
        )

        if self._source_setup_callback:
            logger.debug("Running source-setup callback")
            self._source_setup_callback(source)

        if self._live_stream and hasattr(source.props, "is_live"):
            gst_logger.debug("Enabling live stream mode")
            source = cast(GstBase.BaseSrc, source)
            source.set_live(True)

        setup_proxy(source, self._config["proxy"])

    def _on_gst_bus_message(self, message: GstBusMessage) -> None:
        # Runs on whichever GStreamer thread posted the message. Hand it to
        # the actor thread, so that all message handling is single threaded.
        try:
            self.actor_ref.tell(message)
        except pykka.ActorDeadError:
            # The pipeline outlives the actor for a moment at teardown.
            gst_logger.debug("Dropped bus message, the audio actor is gone.")

    @override
    def on_receive(self, message: Any) -> None:
        match message:
            case GstAsyncDone():
                self._on_gst_async_done()
            case GstBuffering(percent, mode):
                self._on_gst_buffering(percent, mode)
            case GstEndOfStream():
                self._on_gst_end_of_stream()
            case GstError(error, debug):
                self._on_gst_error(error, debug)
            case GstMissingPlugin(description, installer_detail):
                self._on_gst_missing_plugin(description, installer_detail)
            case GstStateChanged(old_state, new_state, pending_state):
                self._on_gst_state_changed(old_state, new_state, pending_state)
            case GstStreamStart():
                self._on_gst_stream_start()
            case GstTag(tags):
                self._on_gst_tag(tags)
            case GstWarning(error, debug):
                self._on_gst_warning(error, debug)

    def _on_gst_state_changed(
        self,
        old_state: Gst.State,
        new_state: Gst.State,
        pending_state: Gst.State,
    ) -> None:
        gst_logger.debug(
            "Got STATE_CHANGED bus message: old=%s new=%s pending=%s",
            old_state.value_name,
            new_state.value_name,
            pending_state.value_name,
        )

        if new_state == Gst.State.READY and pending_state == Gst.State.NULL:
            # HACK: We're not called on the last state change when going down to
            # NULL, so we rewrite the second to last call to get the expected
            # behavior.
            new_state = Gst.State.NULL
            pending_state = Gst.State.VOID_PENDING

        if pending_state != Gst.State.VOID_PENDING:
            return  # Ignore intermediate state changes

        if new_state == Gst.State.READY:
            return  # Ignore READY state as it's GStreamer specific

        new_playback_state = _GST_STATE_MAPPING[new_state]
        old_playback_state, self.state = self.state, new_playback_state

        if self._target_state == Gst.State.READY:
            # READY is GStreamer specific and has no playback state of its
            # own. We are between tracks, so there is no target to report.
            return

        target_playback_state = _GST_STATE_MAPPING[self._target_state]
        if target_playback_state == new_playback_state:
            target_playback_state = None

        logger.debug(
            "Audio event: state_changed(old_state=%s, new_state=%s, target_state=%s)",
            old_playback_state,
            new_playback_state,
            target_playback_state,
        )
        AudioListener.send(
            "state_changed",
            old_state=old_playback_state,
            new_state=new_playback_state,
            target_state=target_playback_state,
        )
        if new_playback_state == PlaybackState.STOPPED:
            logger.debug("Audio event: stream_changed(uri=None)")
            AudioListener.send("stream_changed", uri=None)

        if "GST_DEBUG_DUMP_DOT_DIR" in os.environ:
            assert self._pipeline
            self._pipeline.debug_to_dot_file("mopidy")

    def _on_gst_buffering(self, percent: int, mode: Gst.BufferingMode) -> None:
        assert self._pipeline

        if self._target_state < Gst.State.PAUSED:
            gst_logger.debug("Skip buffering during track change.")
            return

        if mode == Gst.BufferingMode.LIVE:
            return  # Live sources stall in paused.

        level = logs.TRACE_LOG_LEVEL
        if percent < 10 and not self._buffering:
            self._pipeline.set_state(Gst.State.PAUSED)
            self._buffering = True
            level = logging.DEBUG
        if percent == 100:
            self._buffering = False
            if self._target_state == Gst.State.PLAYING:
                self._pipeline.set_state(Gst.State.PLAYING)
            level = logging.DEBUG

        gst_logger.log(level, "Got BUFFERING bus message: percent=%d%%", percent)

    def _on_gst_end_of_stream(self) -> None:
        gst_logger.debug("Got EOS (end of stream) bus message.")
        logger.debug("Audio event: reached_end_of_stream()")
        self._tags = {}
        AudioListener.send("reached_end_of_stream")

    def _on_gst_error(self, error: GLib.Error, debug: str) -> None:
        gst_logger.error(f"GStreamer error: {error.message}")
        gst_logger.debug(f"Got ERROR bus message: error={error!r} debug={debug!r}")

        # TODO: is this needed?
        self.stop_playback()

    def _on_gst_warning(self, error: GLib.Error, debug: str) -> None:
        gst_logger.warning(f"GStreamer warning: {error.message}")
        gst_logger.debug(f"Got WARNING bus message: error={error!r} debug={debug!r}")

    def _on_gst_async_done(self) -> None:
        gst_logger.debug("Got ASYNC_DONE bus message.")

    def _on_gst_tag(self, tags: dict[str, list[Any]]) -> None:
        gst_logger.debug(f"Got TAG bus message: tags={tags_lib.repr_tags(tags)}")

        # Postpone emitting tags until stream start.
        if self._pending_tags is not None:
            self._pending_tags.update(tags)
            return

        # TODO: Add proper tests for only emitting changed tags.
        unique = object()
        changed = []
        for key, value in tags.items():
            # Update any tags that changed, and store changed keys.
            if self._tags.get(key, unique) != value:
                self._tags[key] = value
                changed.append(key)

        if changed:
            logger.debug("Audio event: tags_changed(tags=%r)", changed)
            AudioListener.send("tags_changed", tags=changed)

    def _on_gst_missing_plugin(
        self,
        description: str,
        installer_detail: str | None,
    ) -> None:
        gst_logger.debug("Got missing-plugin bus message: description=%r", description)
        logger.warning("Could not find a %s to handle media.", description)
        if GstPbutils.install_plugins_supported():
            logger.info(
                "You might be able to fix this by running: 'gst-installer \"%s\"'",
                installer_detail,
            )
        # TODO: store the missing plugins installer info in a file so we can
        # can provide a 'mopidy install-missing-plugins' if the system has the
        # required helper installed?

    def _on_gst_stream_start(self) -> None:
        gst_logger.debug("Got STREAM_START bus message")
        uri = self._pending_uri
        logger.debug("Audio event: stream_changed(uri=%r)", uri)
        AudioListener.send("stream_changed", uri=uri)

        # Emit any postponed tags that we got after about-to-finish.
        tags, self._pending_tags = self._pending_tags, None
        self._tags = tags or {}

        if tags:
            logger.debug("Audio event: tags_changed(tags=%r)", tags.keys())
            AudioListener.send("tags_changed", tags=tags.keys())

    def _on_gst_position(self, position: DurationMs) -> None:
        logger.debug("Audio event: position_changed(position=%r)", position)
        AudioListener.send("position_changed", position=position)

    @override
    def set_uri(
        self,
        uri: str,
        live_stream: bool = False,
        download: bool = False,
    ) -> None:
        assert self._pipeline

        # HACK: Hack to workaround issue on Mac OS X where volume level
        # does not persist between track changes. mopidy/mopidy#886
        current_volume = self.mixer.get_volume() if self.mixer is not None else None

        if live_stream and download:
            logger.warning(
                "Ambiguous buffering flags: "
                "'live_stream' and 'download' should not both be set.",
            )

        self._pending_uri = uri
        self._pending_tags = {}
        self._live_stream = live_stream
        self._pipeline.set_uri(uri, download=download)

        if self.mixer is not None and current_volume is not None:
            self.mixer.set_volume(current_volume)

    @override
    def set_source_setup_callback(
        self,
        callback: Callable[[Gst.Element], None],
    ) -> None:
        self._source_setup_callback = callback

    @override
    def set_about_to_finish_callback(
        self,
        callback: Callable[[], None],
    ) -> None:
        self._about_to_finish_callback = callback

    @override
    def get_position(self) -> DurationMs:
        assert self._pipeline

        return self._pipeline.get_position()

    @override
    def set_position(self, position: DurationMs) -> bool:
        assert self._pipeline

        return self._pipeline.seek(position)

    @override
    def start_playback(self) -> bool:
        assert self._pipeline

        self._target_state = Gst.State.PLAYING
        return self._pipeline.set_state(Gst.State.PLAYING)

    @override
    def pause_playback(self) -> bool:
        assert self._pipeline

        self._target_state = Gst.State.PAUSED
        return self._pipeline.set_state(Gst.State.PAUSED)

    @override
    def prepare_change(self) -> bool:
        # This function *MUST* be called before changing URIs or doing
        # changes like updating data that is being pushed. The reason for this
        # is that GStreamer will reset all its state when it changes to
        # `Gst.State.READY`.
        assert self._pipeline

        self._buffering = False
        self._target_state = Gst.State.READY
        return self._pipeline.set_state(Gst.State.READY)

    @override
    def stop_playback(self) -> bool:
        assert self._pipeline

        self._buffering = False
        self._target_state = Gst.State.NULL
        return self._pipeline.set_state(Gst.State.NULL)

    @override
    def get_current_tags(self) -> dict[str, list[Any]]:
        # TODO: should this be a (deep) copy? most likely yes
        # TODO: should we return None when stopped?
        # TODO: support only fetching keys we care about?
        return self._tags

    @override
    def testing_gst__wait_for_state_change(self) -> None:
        assert self._pipeline

        self._pipeline.wait_for_state_change()
