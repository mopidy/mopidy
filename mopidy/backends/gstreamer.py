import logging

import gst

from mopidy import config
from mopidy.backends import BaseBackend
from mopidy.models import Artist, Album, Track, Playlist

logger = logging.getLogger(u'backends.gstreamer')

class GStreamerBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        super(GStreamerBackend, self).__init__(*args, **kwargs)

        playlist = []
        player = gst.element_factory_make("playbin2", "player")
        fakesink = gst.element_factory_make("fakesink", "fakesink")

        player.set_property("video-sink", fakesink)

        self.player = player

    def _play(self):
        if self._current_track is None:
            return False

        self.player.set_property("uri", self._current_track.uri)
        self.player.set_state(gst.STATE_PLAYING)

        return True

    def _stop(self):
        self.player.set_state(gst.STATE_NULL)

        return True

    def playlist_add_track(self, uri, pos=None):
        tracks = self._current_playlist.tracks
        tracks.insert(pos or -1, Track(uri))

        self._current_playlist = Playlist(tracks=tracks)
