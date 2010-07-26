from mopidy.backends import (BaseBackend, BaseCurrentPlaylistController,
    BasePlaybackController, BaseLibraryController,
    BaseStoredPlaylistsController)
from mopidy.models import Playlist, Track

class MockBackend(BaseBackend):
    """
    A backend which implements the backend API in the simplest way possible.
    Used in tests of the frontends.

    Handles URIs starting with ``mock:``.
    """

    def __init__(self, *args, **kwargs):
        super(MockBackend, self).__init__(*args, **kwargs)
        self.current_playlist = MockCurrentPlaylistController(backend=self)
        self.library = MockLibraryController(backend=self)
        self.playback = MockPlaybackController(backend=self)
        self.stored_playlists = MockStoredPlaylistsController(backend=self)
        self.uri_handlers = [u'dummy:']

class MockCurrentPlaylistController(BaseCurrentPlaylistController):
    pass

class MockLibraryController(BaseLibraryController):
    _library = []

    def lookup(self, uri):
        matches = filter(lambda t: uri == t.uri, self._library)
        if matches:
            return matches[0]

    def search(self, field, query):
        return Playlist()

    find_exact = search

class MockPlaybackController(BasePlaybackController):
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

class MockStoredPlaylistsController(BaseStoredPlaylistsController):
    def __init__(self, backend):
        self.backend = backend
        playlist = Playlist(name=u'A playlist')
        track = Track(name=u'test', uri=u'mock:asdf', id=u'2')
        playlist._tracks = [track, ] 
        self._playlists = [playlist, ]

    def search(self, query):
        return [Playlist(name=query)]

    def _stored_playlists_listplaylists(self):
        return u'playlist: A playlist\nLast-Modified: 2010-07-18T23:05:35Z'
