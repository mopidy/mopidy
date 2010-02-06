import logging

from mopidy import config
from mopidy.backends import BaseBackend
from mopidy.models import Artist, Album, Track, Playlist

logger = logging.getLogger(u'backends.gstreamer')

class GStreamerBackend(BaseBackend):
    pass
