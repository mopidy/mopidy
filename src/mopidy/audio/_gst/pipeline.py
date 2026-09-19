from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from mopidy import exceptions
from mopidy._lib import process
from mopidy._lib.gi import GLib, Gst
from mopidy.audio._utils import Signals

if TYPE_CHECKING:
    from collections.abc import Callable

    from mopidy.config import Config

logger = logging.getLogger(__name__)

# This logger is only meant for debug logging of low level GStreamer info such
# as callbacks, event, messages and direct interaction with GStreamer such as
# set_state() on a pipeline.
gst_logger = logging.getLogger("mopidy.audio.gst")

GST_PLAY_FLAGS_AUDIO = 0x02
GST_PLAY_FLAGS_DOWNLOAD = 0x80


# TODO: expose this as a property on audio when #790 gets further along.
class GstOutputBin(Gst.Bin):
    """A bin that sends its input to one or more audio outputs."""

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


def make_output_bin(output: str) -> Gst.Element:
    """Make the element that the audio sink sends its output to."""
    # We don't want to use outputs for regular testing, so just install
    # an unsynced fakesink when someone asks for a 'testoutput'.
    if output == "testoutput":
        fakesink = Gst.ElementFactory.make("fakesink")
        if fakesink is None:
            msg = "Failed to create GStreamer fakesink element."
            raise exceptions.AudioException(msg)
        return fakesink

    output_bin = GstOutputBin()
    try:
        output_bin.add_output(output)
    except exceptions.AudioException:
        process.exit_process()  # TODO: move this up the chain
    return output_bin


class GstPipeline:
    """The GStreamer element graph used for playback.

    This is the only code that touches the GStreamer elements. It knows
    nothing about Mopidy's playback state, events or backends.
    """

    playbin: Gst.Element
    """The playbin element, which is the root of the graph."""

    output_bin: Gst.Element
    """The element that the audio sink sends its output to."""

    queue: Gst.Element
    """The queue in front of the audio sink. Seek events go here."""

    volume: Gst.Element
    """The volume element, which the software mixer controls."""

    def __init__(
        self,
        config: Config,
        *,
        on_message: Callable[[Gst.Bus, Gst.Message], None],
        on_pad_event: Callable[[Gst.Pad, Gst.PadProbeInfo], Gst.PadProbeReturn],
        on_about_to_finish: Callable[[Gst.Element], None],
        on_source_setup: Callable[[Gst.Element, Gst.Element], None],
    ) -> None:
        self._config = config
        self._signals = Signals()
        self._message_handler_id: int | None = None
        self._event_handler_id: int | None = None
        self._pad: Gst.Pad | None = None

        self.playbin = self._make_playbin(on_about_to_finish, on_source_setup)
        self._setup_message_handling(on_message)
        self.output_bin = make_output_bin(self._config["audio"]["output"])
        self._setup_event_handling(on_pad_event)
        self.queue, self.volume = self._make_audio_sink()

    def _make_playbin(
        self,
        on_about_to_finish: Callable[[Gst.Element], None],
        on_source_setup: Callable[[Gst.Element, Gst.Element], None],
    ) -> Gst.Element:
        playbin = Gst.ElementFactory.make("playbin")
        if playbin is None:
            msg = "Failed to create GStreamer playbin."
            raise exceptions.AudioException(msg)
        playbin.set_property("flags", GST_PLAY_FLAGS_AUDIO)

        # TODO: turn into config values...
        playbin.set_property("buffer-size", 5 << 20)  # 5MB
        playbin.set_property("buffer-duration", 5 * Gst.SECOND)

        self._signals.connect(playbin, "source-setup", on_source_setup)
        self._signals.connect(playbin, "about-to-finish", on_about_to_finish)

        return playbin

    def _make_audio_sink(self) -> tuple[Gst.Element, Gst.Element]:
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
        audio_sink.add(self.output_bin)
        audio_sink.add(volume)

        queue.link(volume)
        volume.link(self.output_bin)

        queue_sink = queue.get_static_pad("sink")
        if queue_sink is None:
            msg = "Failed to get sink from GStreamer queue."
            raise exceptions.AudioException(msg)
        ghost_pad = Gst.GhostPad.new("sink", queue_sink)
        audio_sink.add_pad(ghost_pad)

        self.playbin.set_property("audio-sink", audio_sink)

        return queue, volume

    def _setup_message_handling(
        self,
        on_message: Callable[[Gst.Bus, Gst.Message], None],
    ) -> None:
        if (bus := self.playbin.get_bus()) is None:
            return

        bus.add_signal_watch()
        self._message_handler_id = bus.connect("message", on_message)

    def _setup_event_handling(
        self,
        on_pad_event: Callable[[Gst.Pad, Gst.PadProbeInfo], Gst.PadProbeReturn],
    ) -> None:
        if (pad := self.output_bin.get_static_pad("sink")) is None:
            return

        self._pad = pad
        self._event_handler_id = pad.add_probe(
            Gst.PadProbeType.EVENT_BOTH,
            on_pad_event,
        )

    def enable_sync_handler(
        self,
        on_message: Callable[[Gst.Bus, Gst.Message], None],
    ) -> None:
        """Handle bus messages as they are posted, instead of on the main loop.

        Not part of the API. Only for testing of GstAudio.
        """

        def sync_handler(bus: Gst.Bus, message: Gst.Message) -> Gst.BusSyncReply:
            on_message(bus, message)
            return Gst.BusSyncReply.DROP

        bus = self.playbin.get_bus()
        if bus is None:
            msg = "Failed to get bus from GStreamer playbin."
            raise exceptions.AudioException(msg)

        bus.set_sync_handler(sync_handler)

    def teardown(self) -> None:
        if (bus := self.playbin.get_bus()) is not None:
            bus.remove_signal_watch()
            if self._message_handler_id is not None:
                bus.disconnect(self._message_handler_id)
        self._message_handler_id = None

        if self._pad is not None and self._event_handler_id is not None:
            self._pad.remove_probe(self._event_handler_id)
        self._event_handler_id = None

        self._signals.disconnect(self.playbin, "about-to-finish")
        self._signals.disconnect(self.playbin, "source-setup")
        self.playbin.set_state(Gst.State.NULL)
