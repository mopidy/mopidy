import gobject
gobject.threads_init()
# FIXME make sure we don't get hit by
# http://jameswestby.net/weblog/tech/14-caution-python-multiprocessing-and-glib-dont-mix.html

import pygst
pygst.require('0.10')

import gst
import logging
import threading

from mopidy.backends import * 
from mopidy.models import Playlist

logger = logging.getLogger(u'backends.gstreamer')

class GStreamerMessages(threading.Thread):
    def run(self):
        gobject.MainLoop().run()

message_thread = GStreamerMessages()
message_thread.daemon = True
message_thread.start()

class GStreamerBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        super(GStreamerBackend, self).__init__(*args, **kwargs)

        self.playback = GStreamerPlaybackController(self)
        self.stored_playlists = GStreamerStoredPlaylistsController(self)
        self.current_playlist = BaseCurrentPlaylistController(self)
        self.uri_handlers = [u'file:']


class GStreamerPlaybackController(BasePlaybackController):
    def __init__(self, backend):
        super(GStreamerPlaybackController, self).__init__(backend)

        self._bin = gst.element_factory_make("playbin", "player")
        self._bus = self._bin.get_bus()
        sink = gst.element_factory_make("fakesink", "fakesink")

        # FIXME cleanup fakesink?

        self._bin.set_property("video-sink", sink)
        self._bus.add_signal_watch()
        self._bus_id = self._bus.connect('message', self._message)

        self.stop()

    def _set_state(self, state):
        self._bin.set_state(state)

        result, new, old = self._bin.get_state()

        return new == state

    def _message(self, bus, message):
        if message.type == gst.MESSAGE_EOS:
            self.end_of_track_callback()
        elif message.type == gst.MESSAGE_ERROR:
            self._bin.set_state(gst.STATE_NULL)
            error, debug = message.parse_error()
            logger.error('%s %s', error, debug)

    def _play(self, track):
        self._bin.set_state(gst.STATE_READY)
        self._bin.set_property('uri', track.uri)
        return self._set_state(gst.STATE_PLAYING)

    def _stop(self):
        return self._set_state(gst.STATE_READY)

    def _pause(self):
        return self._set_state(gst.STATE_PAUSED)

    def _resume(self):
        return self._set_state(gst.STATE_PLAYING)

    def _seek(self, time_position):
        self._bin.seek_simple(gst.Format(gst.FORMAT_TIME),
            gst.SEEK_FLAG_FLUSH, time_position * gst.MSECOND)
        self._set_state(gst.STATE_PLAYING)

    @property
    def time_position(self):
        try:
            return self._bin.query_position(gst.FORMAT_TIME)[0] // gst.MSECOND
        except gst.QueryError, e:
            logger.error('time_position failed: %s', e)
            return 0

    def destroy(self):
        bin, self._bin = self._bin, None
        bus, self._bus = self._bus, None

        bus.disconnect(self._bus_id)
        bus.remove_signal_watch()
        bin.get_state()
        bin.set_state(gst.STATE_NULL)

        del bus
        del bin


class GStreamerStoredPlaylistsController(BaseStoredPlaylistsController):
    def create(self, name):
        playlist = Playlist(name=name)
        self._playlists.append(playlist)
        return playlist

    def delete(self, playlist):
        if playlist in self._playlists:
            self._playlists.remove(playlist)

    def rename(self, playlist, name):
        if playlist not in self._playlists:
            return

        renamed = playlist.with_(name=name)
        index = self._playlists.index(playlist)
        self._playlists[index] = renamed

    def save(self, playlist):
        self._playlists.append(playlist)
