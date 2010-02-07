import logging

from mopidy.backends import BaseBackend, BasePlaybackController

logger = logging.getLogger(u'backends.gstreamer')

class GStreamerBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        super(GStreamerBackend, self).__init__(*args, **kwargs)

        self.playback = GStreamerPlaybackController(self)

class GStreamerPlaybackController(BasePlaybackController):
    def __init__(self, backend):
        super(GStreamerPlaybackController, self).__init__(backend)
