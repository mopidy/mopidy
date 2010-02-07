from mopidy.backends import (BaseBackend, BaseCurrentPlaylistController,
    BasePlaybackController, BaseLibraryController,
    BaseStoredPlaylistsController)

class DummyBackend(BaseBackend):
    def __init__(self):
        self.current_playlist = DummyCurrentPlaylistController(backend=self)
        self.library = DummyLibraryController(backend=self)
        self.playback = DummyPlaybackController(backend=self)
        self.stored_playlists = DummyStoredPlaylistsController(backend=self)
        self.uri_handlers = [u'dummy:']

class DummyCurrentPlaylistController(BaseCurrentPlaylistController):
    pass

class DummyLibraryController(BaseLibraryController):
    def search(self, type, query):
        return []

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
    pass
