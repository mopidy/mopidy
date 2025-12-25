from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast, override

import pykka
from pykka.typing import proxy_method

from mopidy import exceptions
from mopidy._lib import logs, process
from mopidy._lib.gi import GLib, Gst, GstBase, GstPbutils
from mopidy.audio import tags as tags_lib
from mopidy.audio._api import Audio
from mopidy.audio._listener import AudioListener
from mopidy.audio._utils import (
    Signals,
    clocktime_to_millisecond,
    millisecond_to_clocktime,
    setup_proxy,
)
from mopidy.types import DurationMs, Percentage, PlaybackState

if TYPE_CHECKING:
    from mopidy._exts.softwaremixer.mixer import SoftwareMixerProxy
    from mopidy.config import Config
    from mopidy.mixer import MixerProxy

logger = logging.getLogger(__name__)

# This logger is only meant for debug logging of low level GStreamer info such
# as callbacks, event, messages and direct interaction with GStreamer such as
# set_state() on a pipeline.
gst_logger = logging.getLogger("mopidy.audio.gst")

_GST_PLAY_FLAGS_AUDIO = 0x02
_GST_PLAY_FLAGS_DOWNLOAD = 0x80

_GST_STATE_MAPPING: dict[Gst.State, PlaybackState] = {
    Gst.State.PLAYING: PlaybackState.PLAYING,
    Gst.State.PAUSED: PlaybackState.PAUSED,
    Gst.State.NULL: PlaybackState.STOPPED,
}


# TODO: expose this as a property on audio when #790 gets further along.
class _Outputs(Gst.Bin):
    def __init__(self) -> None:
        Gst.Bin.__init__(self)
        # TODO(gst1): Set 'outputs' as the Bin name for easier debugging

        tee = Gst.ElementFactory.make("tee")
        if tee is None:
            msg = "Failed to create GStreamer tee."
            raise exceptions.AudioException(msg)
        self._tee = tee
        self.add(self._tee)

        tee_sink = self._tee.get_static_pad("sink")
        if tee_sink is None:
            msg = "Failed to get sink from GStreamer tee."
            raise exceptions.AudioException(msg)
        ghost_pad = Gst.GhostPad.new("sink", tee_sink)
        self.add_pad(ghost_pad)

    def add_output(self, description: str) -> None:
        # NOTE: This only works for pipelines not in use until #790 gets done.
        try:
            output = Gst.parse_bin_from_description(
                description,
                ghost_unlinked_pads=True,
            )
        except GLib.Error as exc:
            logger.error('Failed to create audio output "%s": %s', description, exc)
            msg = f"Failed to create audio output {description!r}"
            raise exceptions.AudioException(msg) from exc

        self._add(output)
        logger.info('Audio output set to "%s"', description)

    def _add(self, element: Gst.Element) -> None:
        self.add(element)

        queue = Gst.ElementFactory.make("queue")
        if queue is None:
            msg = "Failed to create GStreamer queue."
            raise exceptions.AudioException(msg)
        self.add(queue)

        queue.link(element)
        self._tee.link(queue)


class GstSoftwareMixerAdapter:
    _mixer: SoftwareMixerProxy
    _element: Gst.Element | None
    _last_volume: int | None
    _last_mute: bool | None
    _signals: Signals

    def __init__(self, mixer: SoftwareMixerProxy) -> None:
        self._mixer = mixer
        self._element = None
        self._last_volume = None
        self._last_mute = None
        self._signals = Signals()

    def setup(
        self,
        element: Gst.Element,
        gst_mixer: GstSoftwareMixerAdapterProxy,
    ) -> None:
        self._element = element
        self._mixer.setup(gst_mixer)

    def teardown(self) -> None:
        self._signals.clear()
        self._mixer.teardown()

    def get_volume(self) -> Percentage:
        assert self._element
        return Percentage(round(self._element.get_property("volume") * 100))

    def set_volume(self, volume: Percentage) -> None:
        assert self._element
        self._element.set_property("volume", volume / 100.0)
        self._mixer.trigger_volume_changed(self.get_volume())

    def get_mute(self) -> bool:
        assert self._element
        return self._element.get_property("mute")

    def set_mute(self, mute: bool) -> None:
        assert self._element
        self._element.set_property("mute", bool(mute))
        self._mixer.trigger_mute_changed(self.get_mute())


class GstSoftwareMixerAdapterProxy:
    get_volume = proxy_method(GstSoftwareMixerAdapter.get_volume)
    set_volume = proxy_method(GstSoftwareMixerAdapter.set_volume)
    get_mute = proxy_method(GstSoftwareMixerAdapter.get_mute)
    set_mute = proxy_method(GstSoftwareMixerAdapter.set_mute)


class _Handler:
    def __init__(self, audio: GstAudio) -> None:
        self._audio = audio
        self._element: Gst.Element | None = None
        self._pad: Gst.Pad | None = None
        self._message_handler_id: int | None = None
        self._event_handler_id: int | None = None

    def setup_message_handling(self, element: Gst.Element) -> None:
        self._element = element
        if (bus := element.get_bus()) is not None:
            bus.add_signal_watch()
            self._message_handler_id = bus.connect("message", self.on_message)

    def setup_event_handling(self, pad: Gst.Pad) -> None:
        self._pad = pad
        self._event_handler_id = pad.add_probe(
            Gst.PadProbeType.EVENT_BOTH,
            self.on_pad_event,
        )

    def teardown_message_handling(self) -> None:
        if self._element is not None and (bus := self._element.get_bus()) is not None:
            bus.remove_signal_watch()
            if self._message_handler_id is not None:
                bus.disconnect(self._message_handler_id)
        self._message_handler_id = None

    def teardown_event_handling(self) -> None:
        if self._pad is not None and self._event_handler_id is not None:
            self._pad.remove_probe(self._event_handler_id)
        self._event_handler_id = None

    def on_message(self, _bus: Gst.Bus, msg: Gst.Message) -> None:  # noqa: C901
        if msg.type == Gst.MessageType.STATE_CHANGED:
            if msg.src != self._element:
                return
            old_state, new_state, pending_state = msg.parse_state_changed()
            self.on_playbin_state_changed(old_state, new_state, pending_state)
        elif msg.type == Gst.MessageType.BUFFERING:
            self.on_buffering(msg.parse_buffering(), msg.get_structure())
        elif msg.type == Gst.MessageType.EOS:
            self.on_end_of_stream()
        elif msg.type == Gst.MessageType.ERROR:
            error, debug = msg.parse_error()
            self.on_error(error, debug)
        elif msg.type == Gst.MessageType.WARNING:
            error, debug = msg.parse_warning()
            self.on_warning(error, debug)
        elif msg.type == Gst.MessageType.ASYNC_DONE:
            self.on_async_done()
        elif msg.type == Gst.MessageType.TAG:
            taglist = msg.parse_tag()
            self.on_tag(taglist)
        elif msg.type == Gst.MessageType.ELEMENT:
            if GstPbutils.is_missing_plugin_message(msg):
                self.on_missing_plugin(msg)
        elif msg.type == Gst.MessageType.STREAM_START:
            self.on_stream_start()

    def on_pad_event(
        self,
        _pad: Gst.Pad,
        pad_probe_info: Gst.PadProbeInfo,
    ) -> Gst.PadProbeReturn:
        if (event := pad_probe_info.get_event()) is None:
            return Gst.PadProbeReturn.OK
        if event.type == Gst.EventType.SEGMENT:
            self.on_segment(event.parse_segment())
        return Gst.PadProbeReturn.OK

    def on_playbin_state_changed(
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
        old_playback_state, self._audio.state = self._audio.state, new_playback_state

        target_playback_state = _GST_STATE_MAPPING.get(self._audio._target_state)
        if target_playback_state is None:
            # HACK: Workaround for #1430, to be fixed properly by #1222.
            logger.warning("Race condition happened. See #1222 and #1430.")
            return
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
            assert self._audio._playbin
            Gst.debug_bin_to_dot_file(
                bin=cast(Gst.Bin, self._audio._playbin),
                details=Gst.DebugGraphDetails.ALL,
                file_name="mopidy",
            )

    def on_buffering(
        self,
        percent: int,
        structure: Gst.Structure | None = None,
    ) -> None:
        assert self._audio._playbin

        if self._audio._target_state < Gst.State.PAUSED:
            gst_logger.debug("Skip buffering during track change.")
            return

        if structure is not None and structure.has_field("buffering-mode"):
            buffering_mode = structure.get_enum("buffering-mode", Gst.BufferingMode)
            if buffering_mode == Gst.BufferingMode.LIVE:
                return  # Live sources stall in paused.

        level = logs.TRACE_LOG_LEVEL
        if percent < 10 and not self._audio._buffering:
            self._audio._playbin.set_state(Gst.State.PAUSED)
            self._audio._buffering = True
            level = logging.DEBUG
        if percent == 100:
            self._audio._buffering = False
            if self._audio._target_state == Gst.State.PLAYING:
                self._audio._playbin.set_state(Gst.State.PLAYING)
            level = logging.DEBUG

        gst_logger.log(level, "Got BUFFERING bus message: percent=%d%%", percent)

    def on_end_of_stream(self) -> None:
        gst_logger.debug("Got EOS (end of stream) bus message.")
        logger.debug("Audio event: reached_end_of_stream()")
        self._audio._tags = {}
        AudioListener.send("reached_end_of_stream")

    def on_error(self, error: GLib.Error, debug: str) -> None:
        gst_logger.error(f"GStreamer error: {error.message}")
        gst_logger.debug(f"Got ERROR bus message: error={error!r} debug={debug!r}")

        # TODO: is this needed?
        self._audio.stop_playback()

    def on_warning(self, error: GLib.Error, debug: str) -> None:
        gst_logger.warning(f"GStreamer warning: {error.message}")
        gst_logger.debug(f"Got WARNING bus message: error={error!r} debug={debug!r}")

    def on_async_done(self) -> None:
        gst_logger.debug("Got ASYNC_DONE bus message.")

    def on_tag(self, taglist: Gst.TagList) -> None:
        tags = tags_lib.convert_taglist(taglist)
        gst_logger.debug(f"Got TAG bus message: tags={tags_lib.repr_tags(tags)}")

        # Postpone emitting tags until stream start.
        if self._audio._pending_tags is not None:
            self._audio._pending_tags.update(tags)
            return

        # TODO: Add proper tests for only emitting changed tags.
        unique = object()
        changed = []
        for key, value in tags.items():
            # Update any tags that changed, and store changed keys.
            if self._audio._tags.get(key, unique) != value:
                self._audio._tags[key] = value
                changed.append(key)

        if changed:
            logger.debug("Audio event: tags_changed(tags=%r)", changed)
            AudioListener.send("tags_changed", tags=changed)

    def on_missing_plugin(self, msg: Gst.Message) -> None:
        desc = GstPbutils.missing_plugin_message_get_description(msg)
        debug = GstPbutils.missing_plugin_message_get_installer_detail(msg)
        gst_logger.debug("Got missing-plugin bus message: description=%r", desc)
        logger.warning("Could not find a %s to handle media.", desc)
        if GstPbutils.install_plugins_supported():
            logger.info(
                "You might be able to fix this by running: 'gst-installer \"%s\"'",
                debug,
            )
        # TODO: store the missing plugins installer info in a file so we can
        # can provide a 'mopidy install-missing-plugins' if the system has the
        # required helper installed?

    def on_stream_start(self) -> None:
        assert self._audio._playbin

        gst_logger.debug("Got STREAM_START bus message")
        uri = self._audio._pending_uri
        logger.debug("Audio event: stream_changed(uri=%r)", uri)
        AudioListener.send("stream_changed", uri=uri)

        # Emit any postponed tags that we got after about-to-finish.
        tags, self._audio._pending_tags = self._audio._pending_tags, None
        self._audio._tags = tags or {}

        if tags:
            logger.debug("Audio event: tags_changed(tags=%r)", tags.keys())
            AudioListener.send("tags_changed", tags=tags.keys())

        if self._audio._pending_metadata:
            self._audio._playbin.send_event(self._audio._pending_metadata)
            self._audio._pending_metadata = None

    def on_segment(self, segment: Gst.Segment) -> None:
        gst_logger.debug(
            "Got SEGMENT pad event: "
            "rate=%(rate)s format=%(format)s start=%(start)s stop=%(stop)s "
            "position=%(position)s",
            {
                "rate": segment.rate,
                "format": Gst.Format.get_name(segment.format),
                "start": segment.start,
                "stop": segment.stop,
                "position": segment.position,
            },
        )
        position_ms = segment.position // Gst.MSECOND
        logger.debug("Audio event: position_changed(position=%r)", position_ms)
        AudioListener.send("position_changed", position=position_ms)


# TODO: create a player class which replaces the actors internals
class GstAudio(Audio, pykka.ThreadingActor):
    """Audio output through `GStreamer <https://gstreamer.freedesktop.org/>`_."""

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
        self._pending_metadata = None

        self._playbin: Gst.Element | None = None
        self._outputs = None
        self._queue = None
        self._about_to_finish_callback: Callable | None = None
        self._source_setup_callback: Callable | None = None

        self._handler = _Handler(self)
        self._signals = Signals()

        if mixer and self._config["audio"]["mixer"] == "software":
            mixer = cast("SoftwareMixerProxy", mixer)
            self.mixer = pykka.traversable(GstSoftwareMixerAdapter(mixer))

    def on_start(self) -> None:
        self._thread = threading.current_thread()
        try:
            self._setup_preferences()
            self._setup_playbin()
            self._setup_outputs()
            self._setup_audio_sink()
        except GLib.Error:
            logger.exception("Unknown GLib error on audio startup.")
            process.exit_process()

    def on_stop(self) -> None:
        self._teardown_mixer()
        self._teardown_playbin()

    def _setup_preferences(self) -> None:
        # TODO: move out of audio actor?
        # Fix for https://github.com/mopidy/mopidy/issues/604
        registry = Gst.Registry.get()
        jacksink = registry.find_feature("jackaudiosink", Gst.ElementFactory)
        if jacksink:
            jacksink.set_rank(Gst.Rank.SECONDARY)

    def _setup_playbin(self) -> None:
        playbin = Gst.ElementFactory.make("playbin")
        if playbin is None:
            msg = "Failed to create GStreamer playbin."
            raise exceptions.AudioException(msg)
        playbin.set_property("flags", _GST_PLAY_FLAGS_AUDIO)

        # TODO: turn into config values...
        playbin.set_property("buffer-size", 5 << 20)  # 5MB
        playbin.set_property("buffer-duration", 5 * Gst.SECOND)

        self._signals.connect(playbin, "source-setup", self._on_source_setup)
        self._signals.connect(playbin, "about-to-finish", self._on_about_to_finish)

        self._playbin = playbin
        self._handler.setup_message_handling(playbin)

    def _teardown_playbin(self) -> None:
        self._handler.teardown_message_handling()
        self._handler.teardown_event_handling()
        if self._playbin is not None:
            self._signals.disconnect(self._playbin, "about-to-finish")
            self._signals.disconnect(self._playbin, "source-setup")
            self._playbin.set_state(Gst.State.NULL)

    def _setup_outputs(self) -> None:
        # We don't want to use outputs for regular testing, so just install
        # an unsynced fakesink when someone asks for a 'testoutput'.
        if self._config["audio"]["output"] == "testoutput":
            fakesink = Gst.ElementFactory.make("fakesink")
            if fakesink is None:
                msg = "Failed to create GStreamer fakesink element."
                raise exceptions.AudioException(
                    msg,
                )
            self._outputs = fakesink
        else:
            self._outputs = _Outputs()
            try:
                self._outputs.add_output(self._config["audio"]["output"])
            except exceptions.AudioException:
                process.exit_process()  # TODO: move this up the chain

        if sink_pad := self._outputs.get_static_pad("sink"):
            self._handler.setup_event_handling(sink_pad)

    def _setup_audio_sink(self) -> None:
        assert self._playbin

        if self._outputs is None:
            msg = "Audio outputs must be set up before audio sinks."
            raise TypeError(msg)

        audio_sink = Gst.ElementFactory.make("bin", "audio-sink")
        if audio_sink is None:
            msg = "Failed to create GStreamer bin 'audio-sink'."
            raise exceptions.AudioException(msg)
        audio_sink = cast(Gst.Bin, audio_sink)

        queue = Gst.ElementFactory.make("queue")
        if queue is None:
            msg = "Failed to create GStreamer queue element."
            raise exceptions.AudioException(msg)

        volume = Gst.ElementFactory.make("volume")
        if volume is None:
            msg = "Failed to create GStreamer volume element."
            raise exceptions.AudioException(msg)

        # Queue element to buy us time between the about-to-finish event and
        # the actual switch, i.e. about to switch can block for longer thanks
        # to this queue.

        # TODO: See if settings should be set to minimize latency. Previous
        # setting breaks appsrc (which we no longer use), and settings before
        # that broke on a few systems. So leave the default to play it safe.
        buffer_time = self._config["audio"]["buffer_time"]
        if buffer_time is not None and buffer_time > 0:
            queue.set_property("max-size-time", buffer_time * Gst.MSECOND)

        audio_sink.add(queue)
        audio_sink.add(self._outputs)
        audio_sink.add(volume)

        queue.link(volume)
        volume.link(self._outputs)

        if self.mixer:
            self.mixer.setup(volume, self.actor_ref.proxy().mixer)

        queue_sink = queue.get_static_pad("sink")
        if queue_sink is None:
            msg = "Failed to get sink from GStreamer queue."
            raise exceptions.AudioException(msg)
        ghost_pad = Gst.GhostPad.new("sink", queue_sink)
        audio_sink.add_pad(ghost_pad)

        self._playbin.set_property("audio-sink", audio_sink)
        self._queue = queue

    def _teardown_mixer(self) -> None:
        if self.mixer:
            self.mixer.teardown()

    def _on_about_to_finish(self, _element: Gst.Element) -> None:
        if self._thread == threading.current_thread():
            logger.error("about-to-finish in actor, aborting to avoid deadlock.")
            return

        gst_logger.debug("Got about-to-finish event.")
        if self._about_to_finish_callback:
            logger.debug("Running about-to-finish callback.")
            self._about_to_finish_callback()

    def _on_source_setup(
        self,
        _element: Gst.Element,
        source: Gst.Element,
    ) -> None:
        gst_logger.debug(
            "Got source-setup signal: element=%s",
            source.__class__.__name__,
        )

        source_factory = source.get_factory()
        if source_factory is None:
            msg = "Failed to get factory from GStreamer source."
            raise exceptions.AudioException(msg)

        if self._source_setup_callback:
            logger.debug("Running source-setup callback")
            self._source_setup_callback(source)

        if self._live_stream and hasattr(source.props, "is_live"):
            gst_logger.debug("Enabling live stream mode")
            source = cast(GstBase.BaseSrc, source)
            source.set_live(True)

        setup_proxy(source, self._config["proxy"])

    @override
    def set_uri(
        self,
        uri: str,
        live_stream: bool = False,
        download: bool = False,
    ) -> None:
        assert self._playbin

        # HACK: Hack to workaround issue on Mac OS X where volume level
        # does not persist between track changes. mopidy/mopidy#886
        current_volume = self.mixer.get_volume() if self.mixer is not None else None

        flags = _GST_PLAY_FLAGS_AUDIO
        if download:
            flags |= _GST_PLAY_FLAGS_DOWNLOAD

        logger.debug(f"Flags: {flags}")
        if live_stream and download:
            logger.warning(
                "Ambiguous buffering flags: "
                "'live_stream' and 'download' should not both be set.",
            )

        self._pending_uri = uri
        self._pending_tags = {}
        self._live_stream = live_stream
        self._playbin.set_property("flags", flags)
        self._playbin.set_property("uri", uri)

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
        assert self._playbin

        success, position = self._playbin.query_position(Gst.Format.TIME)

        if not success:
            # TODO: take state into account for this and possibly also return
            # None as the unknown value instead of zero?
            logger.debug("Position query failed")
            return DurationMs(0)

        return clocktime_to_millisecond(position)

    @override
    def set_position(self, position: DurationMs) -> bool:
        assert self._queue

        # TODO: double check seek flags in use.
        gst_position = millisecond_to_clocktime(position)
        gst_logger.debug("Sending flushing seek: position=%r", gst_position)
        # Send seek event to the queue not the playbin. The default behavior
        # for bins is to forward this event to all sinks. Which results in
        # duplicate seek events making it to appsrc (which we no longer use).
        # Since elements are not allowed to act on the seek event, only modify
        # it, this should be safe to do.
        return self._queue.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH,
            gst_position,
        )

    @override
    def start_playback(self) -> bool:
        return self._set_state(Gst.State.PLAYING)

    @override
    def pause_playback(self) -> bool:
        return self._set_state(Gst.State.PAUSED)

    @override
    def prepare_change(self) -> bool:
        # This function *MUST* be called before changing URIs or doing
        # changes like updating data that is being pushed. The reason for this
        # is that GStreamer will reset all its state when it changes to
        # :attr:`Gst.State.READY`.
        return self._set_state(Gst.State.READY)

    @override
    def stop_playback(self) -> bool:
        return self._set_state(Gst.State.NULL)

    def _set_state(self, state: Gst.State) -> bool:
        """Internal method for setting the raw GStreamer state.

        .. digraph:: gst_state_transitions

            graph [rankdir="LR"];
            node [fontsize=10];

            "NULL" -> "READY"
            "PAUSED" -> "PLAYING"
            "PAUSED" -> "READY"
            "PLAYING" -> "PAUSED"
            "READY" -> "NULL"
            "READY" -> "PAUSED"

        Returns :class:`True` if successful, else :class:`False`.

        :param state: State to set playbin to. One of: `Gst.State.NULL`,
            `Gst.State.READY`, `Gst.State.PAUSED` and `Gst.State.PLAYING`.
        """
        assert self._playbin

        if state < Gst.State.PAUSED:
            self._buffering = False

        self._target_state = state
        result = self._playbin.set_state(state)
        gst_logger.debug(
            "Changing state to %s: result=%s",
            state.value_name,
            result.value_name,
        )

        if result == Gst.StateChangeReturn.FAILURE:
            logger.warning("Setting GStreamer state to %s failed", state.value_name)
            return False
        # TODO: at this point we could already emit stopped event instead
        # of faking it in the message handling when result=OK
        return True

    @override
    def get_current_tags(self) -> dict[str, list[Any]]:
        # TODO: should this be a (deep) copy? most likely yes
        # TODO: should we return None when stopped?
        # TODO: support only fetching keys we care about?
        return self._tags

    @override
    def testing_gst__wait_for_state_change(self) -> None:
        assert self._playbin

        self._playbin.get_state(timeout=Gst.CLOCK_TIME_NONE)

    @override
    def testing_gst__enable_sync_handler(self) -> None:
        assert self._playbin

        def sync_handler(bus: Gst.Bus, message: Gst.Message) -> Gst.BusSyncReply:
            self._handler.on_message(bus, message)
            return Gst.BusSyncReply.DROP

        bus = self._playbin.get_bus()
        if bus is None:
            msg = "Failed to get bus from GStreamer playbin."
            raise exceptions.AudioException(msg)

        bus.set_sync_handler(sync_handler)
