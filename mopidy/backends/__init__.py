import logging
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
