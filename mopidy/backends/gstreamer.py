import logging

import gst

from mopidy.models import Track, Playlist
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
    next_id = 0

    def add(self, uri, at_position=None):
        tracks = self.playlist.tracks

        track = Track(uri=uri, id=self.next_id)

        if at_position is None:
            tracks.append(track)
        else:
            tracks.insert(at_position, track)

        self.next_id += 1
        self.playlist = Playlist(tracks=tracks)

class GStreamerPlaybackController(BasePlaybackController):
    def __init__(self, backend):
        super(GStreamerPlaybackController, self).__init__(backend)

        self.bin = gst.element_factory_make("playbin", "player")
        self.bus = self.bin.get_bus()
        sink = gst.element_factory_make("fakesink", "fakesink")

        self.bin.set_property("video-sink", sink)
        self.stop()

    def _set_state(self, state):
        self.bin.set_state(state)

        result, new, old = self.bin.get_state()

        if new == gst.STATE_PLAYING:
            self.state = self.PLAYING
        elif new == gst.STATE_READY:
            self.state = self.STOPPED
        elif new == gst.STATE_PAUSED:
            self.state = self.PAUSED

    def play(self, track=None, position=None):
        playlist = self.backend.current_playlist.playlist

        if track:
            self.current_track = track
        elif not self.current_track and not playlist.tracks:
            return False
        elif playlist.tracks:
            self.current_track = playlist.tracks[0]

        self.bin.set_state(gst.STATE_READY)
        self.bin.set_property('uri', self.current_track.uri)
        self._set_state(gst.STATE_PLAYING)

        return self.state == self.PLAYING

    def stop(self):
        self._set_state(gst.STATE_READY)

    def pause(self):
        if self.state == self.PLAYING:
            self._set_state(gst.STATE_PAUSED)

    def resume(self):
        if self.state == self.STOPPED:
            self.play()
        else:
            self._set_state(gst.STATE_PLAYING)

    def seek(self, time_position):
        if self.state == self.STOPPED:
            self.play()

        if time_position < 0:
            time_position = 0

        self.bin.seek_simple(gst.Format(gst.FORMAT_TIME),
            gst.SEEK_FLAG_FLUSH, time_position * gst.MSECOND)
        self._set_state(gst.STATE_PLAYING)

    @property
    def volume(self):
        return int(self.bin.get_property('volume') * 100)

    @volume.setter
    def volume(self, value):
        return self.bin.set_property('volume', float(value) / 100)

    @property
    def time_position(self):
        try:
            return self.bin.query_position(gst.FORMAT_TIME)[0] // gst.MSECOND
        except gst.QueryError:
            return 0

    def destroy(self):
        self.bin.set_state(gst.STATE_NULL)
        del self.bin
