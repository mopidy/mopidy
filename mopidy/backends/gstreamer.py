import logging

import gst

from mopidy.backends import (BaseBackend,
                             BasePlaybackController,
                             BaseCurrentPlaylistController)

logger = logging.getLogger(u'backends.gstreamer')

class GStreamerBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        super(GStreamerBackend, self).__init__(*args, **kwargs)

        self.playback = GStreamerPlaybackController(self)
        self.current_playlist = GStreamerCurrentPlaylistController(self)

class GStreamerCurrentPlaylistController(BaseCurrentPlaylistController):
    pass

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

    def play(self, id=None, position=None):
        if not self.current_track:
            return False

        self.bin.set_property("uri", self.current_track.uri)
        self.bin.set_state(self.PLAYING)

        return True
