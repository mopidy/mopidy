import logging
import random
import time

from mopidy.exceptions import MpdNotImplemented
from mopidy.models import Playlist

logger = logging.getLogger('backends.base')

class BaseBackend(object):
    current_playlist = None
    library = None
    playback = None
    stored_playlists = None
    uri_handlers = []

    def destroy(self):
        self.playback.destroy()

class BaseCurrentPlaylistController(object):
    def __init__(self, backend):
        self.backend = backend
        self.version = 0
        self.playlist = Playlist()

    @property
    def playlist(self):
        return self._playlist

    @playlist.setter
    def playlist(self, playlist):
        self._playlist = playlist
        self.version += 1
        self.backend.playback.new_playlist_loaded_callback()

    def add(self, uri, at_position=None):
        raise NotImplementedError

    def clear(self):
        self.backend.playback.stop()
        self.playlist = Playlist()

    def get_by_id(self, id):
        matches = filter(lambda t: t.id == id, self.playlist.tracks)
        if matches:
            return matches[0]
        else:
            raise KeyError('Track with ID "%s" not found' % id)

    def get_by_url(self, uri):
        matches = filter(lambda t: t.uri == uri, self.playlist.tracks)
        if matches:
            return matches[0]
        else:
            raise KeyError('Track with URI "%s" not found' % uri)

    def load(self, playlist):
        self.playlist = playlist

    def move(self, start, end, to_position):
        tracks = self.playlist.tracks

        if start == end:
            end += 1

        new_tracks = tracks[:start] + tracks[end:]

        for track in tracks[start:end]:
            new_tracks.insert(to_position, track)
            to_position += 1

        self.playlist = Playlist(tracks=new_tracks)

    def remove(self,track):
        tracks = filter(lambda t: t != track, self.playlist.tracks)

        self.playlist = Playlist(tracks=tracks)

    def shuffle(self, start=None, end=None):
        tracks = self.playlist.tracks

        before = tracks[:start or 0]
        shuffled = tracks[start:end]
        after = tracks[end or len(tracks):]

        random.shuffle(shuffled)

        self.playlist = Playlist(tracks=before+shuffled+after)

class BasePlaybackController(object):
    PAUSED = 'paused'
    PLAYING = 'playing'
    STOPPED = 'stopped'

    state = STOPPED
    repeat = False
    random = False
    consume = False
    volume = None
    
    def __init__(self, backend):
        self.backend = backend
        self.current_track = None
        self._shuffled = []

    def play(self, id=None, position=None):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def new_playlist_loaded_callback(self):
        self.current_track = None

        if self.state == self.PLAYING:
            self.play()
        elif self.state == self.PAUSED:
            self.stop()

    def next(self):
        current_track = self.current_track

        if not self.next_track:
            self.stop()
        else:
            self.play(self.next_track)

        if self.consume:
            self.backend.current_playlist.remove(current_track)

    def previous(self):
        if self.previous_track:
            self.play(self.previous_track)

    def pause(self):
        raise NotImplementedError

    def resume(self):
        raise NotImplementedError

    def seek(self, time_position):
        raise NotImplementedError

    @property
    def next_track(self):
        playlist = self.backend.current_playlist.playlist

        if not playlist.tracks:
            return None

        if self.random and not self._shuffled:
            self._shuffled = playlist.tracks
            random.shuffle(self._shuffled)

        if self._shuffled:
            return self._shuffled[0]

        if self.current_track is None:
            return playlist.tracks[0]

        if self.repeat:
            position = (self.playlist_position + 1) % len(playlist.tracks)
            return playlist.tracks[position]

        try:
            return playlist.tracks[self.playlist_position + 1]
        except IndexError:
            return None

    @property
    def previous_track(self):
        playlist = self.backend.current_playlist.playlist

        if self.repeat or self.consume or self.random:
            return self.current_track

        if self.current_track is None:
            return None

        if self.playlist_position - 1 < 0:
            return None

        try:
            return playlist.tracks[self.playlist_position - 1]
        except IndexError:
            return None

    @property
    def playlist_position(self):
        playlist = self.backend.current_playlist.playlist

        try:
            return playlist.tracks.index(self.current_track)
        except ValueError:
            return None

    @property
    def time_position(self):
        raise NotImplementedError

    def destroy(self):
        pass
