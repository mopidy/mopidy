from mopidy.backends import (BaseBackend, BaseCurrentPlaylistController,
    BasePlaybackController, BaseLibraryController,
    BaseStoredPlaylistsController)
from mopidy.models import Playlist

class DummyBackend(BaseBackend):
    """
    A backend which implements the backend API in the simplest way possible.
    Used in tests of the frontends.

    Handles URIs starting with ``dummy:``.
    """

    def __init__(self, *args, **kwargs):
        super(DummyBackend, self).__init__(*args, **kwargs)
        self.current_playlist = DummyCurrentPlaylistController(backend=self)
        self.library = DummyLibraryController(backend=self)
        self.playback = DummyPlaybackController(backend=self)
        self.stored_playlists = DummyStoredPlaylistsController(backend=self)
        self.uri_handlers = [u'dummy:']

class DummyCurrentPlaylistController(BaseCurrentPlaylistController):
    pass

class DummyLibraryController(BaseLibraryController):
    _library = []

    def lookup(self, uri):
        matches = filter(lambda t: uri == t.uri, self._library)
        if matches:
            return matches[0]

    def search(self, field, query):
        return Playlist()

    find_exact = search

class DummyPlaybackController(BasePlaybackController):
    def _next(self, track):
        return True

    def _pause(self):
        return True

    def _play(self, track):
        return True

    def _previous(self, track):
        return True

    def _resume(self):
        return True

class DummyStoredPlaylistsController(BaseStoredPlaylistsController):
    def search(self, query):
        return [Playlist(name=query)]
