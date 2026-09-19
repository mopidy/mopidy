from __future__ import annotations

import logging

from mopidy import exceptions
from mopidy._lib import process
from mopidy._lib.gi import GLib, Gst

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
