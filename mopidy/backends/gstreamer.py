import gobject
gobject.threads_init()

import gst
import logging
import threading

from mopidy.models import Track, Playlist
from mopidy.backends import (BaseBackend,
                             BasePlaybackController,
                             BaseCurrentPlaylistController)

logger = logging.getLogger(u'backends.gstreamer')

class GStreamerMessages(threading.Thread):
    def run(self):
        gobject.MainLoop().run()
GStreamerMessages().start()


class GStreamerBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        super(GStreamerBackend, self).__init__(*args, **kwargs)

        self.playback = GStreamerPlaybackController(self)
        self.current_playlist = BaseCurrentPlaylistController(self)


class GStreamerPlaybackController(BasePlaybackController):
    def __init__(self, backend):
        super(GStreamerPlaybackController, self).__init__(backend)

        self._bin = gst.element_factory_make("playbin", "player")
        self._bus = self._bin.get_bus()
        sink = gst.element_factory_make("fakesink", "fakesink")

        self._bin.set_property("video-sink", sink)
        self._bus.add_signal_watch()
        self._bus_id = self._bus.connect('message', self._message)

        self.stop()

    def _set_state(self, state):
        self._bin.set_state(state)

        result, new, old = self._bin.get_state()

        if new == gst.STATE_PLAYING:
            self.state = self.PLAYING
        elif new == gst.STATE_READY:
            self.state = self.STOPPED
        elif new == gst.STATE_PAUSED:
            self.state = self.PAUSED

    def _message(self, bus, message):
        if message.type == gst.MESSAGE_EOS:
            self.next()
        elif message.type == gst.MESSAGE_ERROR:
            self._bin.set_state(gst.STATE_NULL)
            error, debug = message.parse_error()
            logger.error('%s %s', error, debug)

    def play(self, track=None, position=None):
        playlist = self.backend.current_playlist.playlist

        if track:
            self.current_track = track
        elif not self.current_track:
            self.current_track = self.next_track

        if not self.current_track:
            return

        if self.random and self._shuffled:
            self._shuffled.pop(0)

        self._bin.set_state(gst.STATE_READY)
        self._bin.set_property('uri', self.current_track.uri)
        self._set_state(gst.STATE_PLAYING)

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
        elif self.current_track and time_position > self.current_track.length:
            self.next()
            return

        self._bin.seek_simple(gst.Format(gst.FORMAT_TIME),
            gst.SEEK_FLAG_FLUSH, time_position * gst.MSECOND)
        self._set_state(gst.STATE_PLAYING)

    @property
    def volume(self):
        return int(self._bin.get_property('volume') * 100)

    @volume.setter
    def volume(self, value):
        return self._bin.set_property('volume', float(value) / 100)

    @property
    def time_position(self):
        try:
            return self._bin.query_position(gst.FORMAT_TIME)[0] // gst.MSECOND
        except gst.QueryError:
            return 0

    def destroy(self):
        bin, self._bin = self._bin, None
        bus, self._bus = self._bus, None

        bus.disconnect(self._bus_id)
        bus.remove_signal_watch()
        bin.get_state(-1)
        bin.set_state(gst.STATE_NULL)

        del bus
        del bin
