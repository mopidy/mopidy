import time

from mopidy.exceptions import MpdNotImplemented

class BaseBackend(object):
    PLAY = u'play'
    PAUSE = u'pause'
    STOP = u'stop'

    def __init__(self):
        self.state = self.STOP
        self._play_time_accumulated = 0
        self._play_start = False

    def current_song(self):
        return None

# Status methods
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
        return u'%s:%s' % (
            self.status_time_position(), self.status_time_total())

    def status_time_position(self):
        if self.state == self.PAUSE:
            return self._play_time_accumulated
        elif self.state == self.PLAY and self._play_start:
            return self._play_time_accumulated + (
                int(time.time()) - self._play_start)
        else:
            return 0

    def status_time_total(self):
        return 0

    def status_xfade(self):
        return 0

# Control methods
    def next(self):
        self.stop()
        if self._next():
            self.state = self.PLAY
            self._play_time_accumulated = 0
            self._play_start = int(time.time())

    def _next(self):
        raise MpdNotImplemented

    def pause(self):
        if self.state == self.PLAY and self._pause():
            self.state = self.PAUSE
            self._play_time_accumulated += (
                int(time.time()) - self._play_start)

    def _pause(self):
        raise MpdNotImplemented

    def play(self, songpos=None, songid=None):
        if self.state == self.PAUSE and songpos is None and songid is None:
            return self.resume()
        self.stop()
        if songpos is not None:
            result = self._play_pos(songpos)
        elif songid is not None:
            result = self._play_id(songid)
        else:
            result = self._play()
        if result:
            self.state = self.PLAY
            self._play_time_accumulated = 0
            self._play_start = int(time.time())

    def _play(self):
        raise MpdNotImplemented

    def _play_id(self):
        raise MpdNotImplemented

    def _play_pos(self):
        raise MpdNotImplemented

    def previous(self):
        self.stop()
        if self._previous():
            self.state = self.PLAY
            self._play_time_accumulated = 0
            self._play_start = int(time.time())

    def _previous(self):
        raise MpdNotImplemented

    def resume(self):
        if self.state == self.PAUSE and self._resume():
            self.state = self.PLAY
            self._play_start = int(time.time())

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
