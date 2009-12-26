import logging
import time

from mopidy.exceptions import MpdNotImplemented

logger = logging.getLogger('backends.base')

class BaseBackend(object):
    PLAY = u'play'
    PAUSE = u'pause'
    STOP = u'stop'

    @property
    def state(self):
        if not hasattr(self, '_state'):
            self._state = self.STOP
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

# Status methods

    def current_song(self):
        return None

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
        return 0

    def status_playlist(self):
        return 0

    def status_playlist_length(self):
        return 0

    def status_state(self):
        return self.state

    def status_time(self):
        return u'%s:%s' % (self._play_time_elapsed, self.status_time_total())

    def status_time_total(self):
        return 0

    def status_xfade(self):
        return 0

# Control methods

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
        pass

    def playlist_info(self, songpos, start, end):
        return None

# Stored playlist methods

    def playlists_list(self):
        return None

# Music database methods

    def search(self, type, what):
        return None
