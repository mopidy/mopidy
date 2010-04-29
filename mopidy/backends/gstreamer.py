import gobject
gobject.threads_init()
# FIXME make sure we don't get hit by
# http://jameswestby.net/weblog/tech/14-caution-python-multiprocessing-and-glib-dont-mix.html

import pygst
pygst.require('0.10')

import gst
import logging
import os
import glob
import shutil
import threading

from mopidy.backends import *
from mopidy.models import Playlist, Track
from mopidy import settings
from mopidy.utils import parse_m3u

logger = logging.getLogger(u'backends.gstreamer')

class GStreamerMessages(threading.Thread):
    def run(self):
        gobject.MainLoop().run()

message_thread = GStreamerMessages()
message_thread.daemon = True
message_thread.start()

class GStreamerBackend(BaseBackend):
    """
    A backend for playing music from a local music archive.

    Uses the `GStreamer <http://gstreamer.freedesktop.org/>`_ library.
    """

    def __init__(self, *args, **kwargs):
        super(GStreamerBackend, self).__init__(*args, **kwargs)

        self.playback = GStreamerPlaybackController(self)
        self.stored_playlists = GStreamerStoredPlaylistsController(self)
        self.current_playlist = BaseCurrentPlaylistController(self)
        self.library = GStreamerLibraryController(self)
        self.uri_handlers = [u'file://']


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
        bus.set_flushing(True)

        del bus
        del bin


class GStreamerStoredPlaylistsController(BaseStoredPlaylistsController):
    def __init__(self, *args):
        super(GStreamerStoredPlaylistsController, self).__init__(*args)
        self._folder = os.path.expanduser(settings.PLAYLIST_FOLDER)
        self.refresh()

    def refresh(self):
        playlists = []

        for m3u in glob.glob(os.path.join(self._folder, '*.m3u')):
            name = os.path.basename(m3u)[:len('.m3u')]
            track_uris = parse_m3u(m3u)
            tracks = map(lambda u: Track(uri=u), track_uris)
            playlist = Playlist(tracks=tracks, name=name)

            # FIXME playlist name needs better handling
            # FIXME tracks should come from lib. lookup

            playlists.append(playlist)

        self.playlists = playlists

    def create(self, name):
        playlist = Playlist(name=name)
        self.save(playlist)
        return playlist

    def delete(self, playlist):
        if playlist not in self._playlists:
            return

        self._playlists.remove(playlist)
        file = os.path.join(self._folder, playlist.name + '.m3u')

        if os.path.exists(file):
            os.remove(file)

    def rename(self, playlist, name):
        if playlist not in self._playlists:
            return

        src = os.path.join(self._folder, playlist.name + '.m3u')
        dst = os.path.join(self._folder, name + '.m3u')

        renamed = playlist.with_(name=name)
        index = self._playlists.index(playlist)
        self._playlists[index] = renamed

        shutil.move(src, dst)

    def save(self, playlist):
        file_path = os.path.join(self._folder, playlist.name + '.m3u')

        # FIXME this should be a save_m3u function, not inside save
        with open(file_path, 'w') as file:
            for track in playlist.tracks:
                if track.uri.startswith('file://'):
                    file.write(track.uri[len('file://'):] + '\n')
                else:
                    file.write(track.uri + '\n')

        self._playlists.append(playlist)


class GStreamerLibraryController(BaseLibraryController):
    def refresh(self, uri=None):
        pass
