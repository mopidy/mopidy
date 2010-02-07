import logging

import gst

from mopidy.backends import BaseBackend, BasePlaybackController

logger = logging.getLogger(u'backends.gstreamer')

class GStreamerBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        super(GStreamerBackend, self).__init__(*args, **kwargs)

        self.playback = GStreamerPlaybackController(self)

class GStreamerPlaybackController(BasePlaybackController):
    PAUSED = gst.STATE_PAUSED
    PLAYING = gst.STATE_PLAYING
    STOPPED = gst.STATE_NULL

    def __init__(self, backend):
        super(GStreamerPlaybackController, self).__init__(backend)

        bin = gst.element_factory_make("playbin", "player")
        sink = gst.element_factory_make("fakesink", "fakesink")

        bin.set_property("video-sink", sink)

        self.bin = bin
