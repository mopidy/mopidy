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

class BaseCurrentPlaylistController(object):
    def __init__(self, backend):
        self.backend = backend
        self.playlist = Playlist()

    def add(self, uri, at_position=None):
        raise NotImplementedError

    def clear(self):
        self.backend.playback.stop()
        self.playlist = Playlist()

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

    def remove(self, position):
        tracks = self.playlist.tracks
        del tracks[position]

        self.playlist = Playlist(tracks=tracks)

    def shuffle(self, start=None, end=None):
        tracks = self.playlist.tracks
        random.shuffle(tracks)

        self.playlist = Playlist(tracks=tracks)

class BasePlaybackController(object):
    PAUSED = 'paused'
    PLAYING = 'playing'
    STOPPED = 'stopped'

    state = STOPPED
    
    def __init__(self, backend):
        self.backend = backend
        self.current_track = None
        self.playlist_position = 0

    def play(self, id=None, position=None):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def next(self):
        raise NotImplementedError
