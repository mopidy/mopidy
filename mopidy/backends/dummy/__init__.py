from mopidy.backends.base import (BaseBackend, BaseCurrentPlaylistController,
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

    def find_exact(self, **query):
        return Playlist()

    def lookup(self, uri):
        matches = filter(lambda t: uri == t.uri, self._library)
        if matches:
            return matches[0]

    def refresh(self, uri=None):
        pass

    def search(self, **query):
        return Playlist()


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

    def _seek(self, time_position):
        return True

    def _stop(self):
        return True

    def _trigger_started_playing_event(self):
        pass # noop

    def _trigger_stopped_playing_event(self):
        pass # noop


class DummyStoredPlaylistsController(BaseStoredPlaylistsController):
    _playlists = []

    def create(self, name):
        playlist = Playlist(name=name)
        self._playlists.append(playlist)
        return playlist

    def delete(self, playlist):
        self._playlists.remove(playlist)

    def lookup(self, uri):
        return filter(lambda p: p.uri == uri, self._playlists)

    def refresh(self):
        pass

    def rename(self, playlist, new_name):
        self._playlists[self._playlists.index(playlist)] = \
            playlist.with_(name=new_name)

    def save(self, playlist):
        self._playlists.append(playlist)
