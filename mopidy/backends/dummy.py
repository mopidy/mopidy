from mopidy.backends import (BaseBackend, BaseCurrentPlaylistController,
    BasePlaybackController, BaseLibraryController,
    BaseStoredPlaylistsController)
from mopidy.models import Playlist

class DummyBackend(BaseBackend):
    def __init__(self):
        self.current_playlist = DummyCurrentPlaylistController(backend=self)
        self.library = DummyLibraryController(backend=self)
        self.playback = DummyPlaybackController(backend=self, mixer=DummyMixer)
        self.stored_playlists = DummyStoredPlaylistsController(backend=self)
        self.uri_handlers = [u'dummy:']

class DummyCurrentPlaylistController(BaseCurrentPlaylistController):
    pass

class DummyLibraryController(BaseLibraryController):
    def search(self, type, query):
        return Playlist()

class DummyPlaybackController(BasePlaybackController):
    def _next(self):
        return True

    def _pause(self):
        return True

    def _play(self, track):
        return True

    def _previous(self):
        return True

    def _resume(self):
        return True

class DummyStoredPlaylistsController(BaseStoredPlaylistsController):
    def search(self, query):
        return [Playlist(name=query)]

class DummyMixer(object):
    volume = 0

    def getvolume(self):
        return [self.volume, self.volume]

    def setvolume(self, volume):
        self.volume = volume
