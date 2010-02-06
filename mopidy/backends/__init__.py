import logging
import time

from mopidy.exceptions import MpdNotImplemented
from mopidy.models import Playlist

logger = logging.getLogger('backends.base')

class BaseBackend(object):
    PLAY = u'play'
    PAUSE = u'pause'
    STOP = u'stop'

    def __init__(self, *args, **kwargs):
        self._state = self.STOP
        self._playlists = []
        self._x_current_playlist = Playlist()
        self._current_playlist_version = 0

# Backend state

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        (old_state, self._state) = (self.state, new_state)
        logger.debug(u'Changing state: %s -> %s', old_state, new_state)
        if old_state in (self.PLAY, self.STOP) and new_state == self.PLAY:
            self._play_time_start()
        elif old_state == self.PLAY and new_state == self.PAUSE:
            self._play_time_pause()
        elif old_state == self.PAUSE and new_state == self.PLAY:
            self._play_time_resume()

    @property
    def _play_time_elapsed(self):
        if self.state == self.PLAY:
            time_since_started = int(time.time()) - self._play_time_started
            return self._play_time_accumulated + time_since_started
        elif self.state == self.PAUSE:
            return self._play_time_accumulated
        elif self.state == self.STOP:
            return 0

    def _play_time_start(self):
        self._play_time_accumulated = 0
        self._play_time_started = int(time.time())

    def _play_time_pause(self):
        time_since_started = int(time.time()) - self._play_time_started
        self._play_time_accumulated += time_since_started

    def _play_time_resume(self):
        self._play_time_started = int(time.time())

    @property
    def _current_playlist(self):
        return self._x_current_playlist

    @_current_playlist.setter
    def _current_playlist(self, playlist):
        self._x_current_playlist = playlist
        self._current_playlist_version += 1

    @property
    def _current_track(self):
        if self._current_song_pos is not None:
            return self._current_playlist.tracks[self._current_song_pos]

    @property
    def _current_song_pos(self):
        if not hasattr(self, '_x_current_song_pos'):
            self._x_current_song_pos = None
        if (self._current_playlist is None
                or self._current_playlist.length == 0):
            self._x_current_song_pos = None
        elif self._x_current_song_pos < 0:
            self._x_current_song_pos = 0
        elif self._x_current_song_pos >= self._current_playlist.length:
            self._x_current_song_pos = self._current_playlist.length - 1
        return self._x_current_song_pos

    @_current_song_pos.setter
    def _current_song_pos(self, songid):
        self._x_current_song_pos = songid

# Status methods

    def current_song(self):
        if self.state is not self.STOP and self._current_track is not None:
            return self._current_track.mpd_format(self._current_song_pos)

    def status_bitrate(self):
        return 0

    def status_consume(self):
        return 0

    def status_volume(self):
        return 0

    def status_repeat(self):
        return 0

    def status_random(self):
        return 0

    def status_single(self):
        return 0

    def status_song_id(self):
        return self._current_song_pos # Override if you got a better ID scheme

    def status_playlist(self):
        return self._current_playlist_version

    def status_playlist_length(self):
        return self._current_playlist.length

    def status_state(self):
        return self.state

    def status_time(self):
        return u'%s:%s' % (self._play_time_elapsed, self.status_time_total())

    def status_time_total(self):
        if self._current_track is not None:
            return self._current_track.length // 1000
        else:
            return 0

    def status_xfade(self):
        return 0

    def url_handlers(self):
        return []

# Control methods

    def end_of_track(self):
        self.next()

    def next(self):
        self.stop()
        if self._next():
            self.state = self.PLAY

    def _next(self):
        raise MpdNotImplemented

    def pause(self):
        if self.state == self.PLAY and self._pause():
            self.state = self.PAUSE

    def _pause(self):
        raise MpdNotImplemented

    def play(self, songpos=None, songid=None):
        if self.state == self.PAUSE and songpos is None and songid is None:
            return self.resume()
        self.stop()
        if songpos is not None and self._play_pos(songpos):
            self.state = self.PLAY
        elif songid is not None and self._play_id(songid):
            self.state = self.PLAY
        elif self._play():
            self.state = self.PLAY

    def _play(self):
        raise MpdNotImplemented

    def _play_id(self, songid):
        raise MpdNotImplemented

    def _play_pos(self, songpos):
        raise MpdNotImplemented

    def previous(self):
        self.stop()
        if self._previous():
            self.state = self.PLAY

    def _previous(self):
        raise MpdNotImplemented

    def resume(self):
        if self.state == self.PAUSE and self._resume():
            self.state = self.PLAY

    def _resume(self):
        raise MpdNotImplemented

    def stop(self):
        if self.state != self.STOP and self._stop():
            self.state = self.STOP

    def _stop(self):
        raise MpdNotImplemented

# Current/single playlist methods

    def playlist_changes_since(self, version):
        return None

    def playlist_load(self, name):
        matches = filter(lambda p: p.name == name, self._playlists)
        if matches:
            self._current_playlist = matches[0]
        else:
            self._current_playlist = None

    def playlist_changes_since(self, version='0'):
        if int(version) < self._current_playlist_version:
            return self._current_playlist.mpd_format()

    def playlist_info(self, songpos=None, start=0, end=None):
        if songpos is not None:
            start = int(songpos)
            end = start + 1
        else:
            if start is None:
                start = 0
            start = int(start)
            if end is not None:
                end = int(end)
        return self._current_playlist.mpd_format(start, end)

# Stored playlist methods

    def playlists_list(self):
        return [u'playlist: %s' % p.name for p in self._playlists]

# Music database methods

    def search(self, type, what):
        return None
