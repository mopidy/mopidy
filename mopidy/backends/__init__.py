from copy import copy
import logging
import random
import time

from mopidy.models import Playlist

logger = logging.getLogger('backends.base')

class BaseBackend(object):
    current_playlist = None
    library = None
    playback = None
    stored_playlists = None
    uri_handlers = []


class BaseCurrentPlaylistController(object):
    def __init__(self, backend):
        self.backend = backend
        self.version = 0
        self.playlist = Playlist()

    @property
    def playlist(self):
        return copy(self._playlist)

    @playlist.setter
    def playlist(self, new_playlist):
        self._playlist = new_playlist
        self.version += 1

    def add(self, uri, at_position=None):
        raise NotImplementedError

    def clear(self):
        self.backend.playback.stop()
        self.playlist = Playlist()

    def get_by_id(self, id):
        matches = filter(lambda t: t.id == id, self._playlist.tracks)
        if matches:
            return matches[0]
        else:
            raise KeyError('Track with ID "%s" not found' % id)

    def get_by_uri(self, uri):
        matches = filter(lambda t: t.uri == uri, self._playlist.tracks)
        if matches:
            return matches[0]
        else:
            raise KeyError('Track with URI "%s" not found' % uri)

    def load(self, playlist):
        self.playlist = playlist
        self.version = 0

    def move(self, start, end, to_position):
        tracks = self.playlist.tracks
        new_tracks = tracks[:start] + tracks[end:]

        for track in tracks[start:end]:
            new_tracks.insert(to_position, track)
            to_position += 1

        self.playlist = self.playlist.with_(tracks=new_tracks)

    def remove(self, position):
        tracks = self.playlist.tracks
        del tracks[position]
        self.playlist = self.playlist.with_(tracks=tracks)

    def shuffle(self, start=None, end=None):
        tracks = self.playlist.tracks

        before = tracks[:start or 0]
        shuffled = tracks[start:end]
        after = tracks[end or len(tracks):]

        random.shuffle(shuffled)

        self.playlist = self.playlist.with_(tracks=before+shuffled+after)


class BaseLibraryController(object):
    def __init__(self, backend):
        self.backend = backend

    def find_exact(self, type, query):
        raise NotImplementedError

    def lookup(self, uri):
        raise NotImplementedError

    def refresh(self, uri=None):
        raise NotImplementedError

    def search(self, type, query):
        raise NotImplementedError


class BasePlaybackController(object):
    PAUSED = u'paused'
    PLAYING = u'playing'
    STOPPED = u'stopped'

    def __init__(self, backend):
        self.backend = backend
        self._state = self.STOPPED
        self.consume = False
        self.current_track = None
        self.random = False
        self.repeat = False
        self.state = self.STOPPED
        self.volume = None

    @property
    def playlist_position(self):
        if self.current_track is None:
            return None
        try:
            return self.backend.current_playlist.playlist.tracks.index(
                self.current_track)
        except ValueError:
            return None

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        (old_state, self._state) = (self.state, new_state)
        logger.debug(u'Changing state: %s -> %s', old_state, new_state)
        if (old_state in (self.PLAYING, self.STOPPED)
                and new_state == self.PLAYING):
            self._play_time_start()
        elif old_state == self.PLAYING and new_state == self.PAUSED:
            self._play_time_pause()
        elif old_state == self.PAUSED and new_state == self.PLAYING:
            self._play_time_resume()

    @property
    def time_position(self):
        if self.state == self.PLAYING:
            time_since_started = int(time.time()) - self._play_time_started
            return self._play_time_accumulated + time_since_started
        elif self.state == self.PAUSED:
            return self._play_time_accumulated
        elif self.state == self.STOPPED:
            return 0

    def _play_time_start(self):
        self._play_time_accumulated = 0
        self._play_time_started = int(time.time())

    def _play_time_pause(self):
        time_since_started = int(time.time()) - self._play_time_started
        self._play_time_accumulated += time_since_started

    def _play_time_resume(self):
        self._play_time_started = int(time.time())

    def new_playlist_loaded_callback(self):
        self.current_track = None
        if self.state == self.PLAYING:
            if self.backend.current_playlist.playlist.length > 0:
                self.play(self.backend.current_playlist.playlist.tracks[0])
            else:
                self.stop()

    def next(self):
        self.stop()
        if self._next():
            self.state = self.PLAYING

    def _next(self):
        raise NotImplementedError

    def pause(self):
        if self.state == self.PLAYING and self._pause():
            self.state = self.PAUSED

    def _pause(self):
        raise NotImplementedError

    def play(self, track=None):
        if self.state == self.PAUSED and track is None:
            return self.resume()
        if track is not None:
            self.current_track = track
        self.stop()
        if self._play(track):
            self.state = self.PLAYING

    def _play(self, track):
        raise NotImplementedError

    def previous(self):
        self.stop()
        if self._previous():
            self.state = self.PLAYING

    def _previous(self):
        raise NotImplementedError

    def resume(self):
        if self.state == self.PAUSED and self._resume():
            self.state = self.PLAYING

    def _resume(self):
        raise NotImplementedError

    def seek(self, time_position):
        raise NotImplementedError

    def stop(self):
        if self.state != self.STOPPED and self._stop():
            self.state = self.STOPPED

    def _stop(self):
        raise NotImplementedError


class BaseStoredPlaylistsController(object):
    def __init__(self, backend):
        self.backend = backend
        self._playlists = []

    @property
    def playlists(self):
        return copy(self._playlists)

    def add(self, uri):
        raise NotImplementedError

    def create(self, name):
        raise NotImplementedError

    def delete(self, playlist):
        raise NotImplementedError

    def lookup(self, uri):
        raise NotImplementedError

    def refresh(self):
        raise NotImplementedError

    def rename(self, playlist, new_name):
        raise NotImplementedError

    def save(self, playlist):
        raise NotImplementedError

    def search(self, query):
        return filter(lambda p: query in p.name, self._playlists)
