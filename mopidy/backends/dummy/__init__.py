from pykka.actor import ThreadingActor

from mopidy import core
from mopidy.backends import base
from mopidy.models import Playlist


class DummyBackend(ThreadingActor, base.Backend):
    """
    A backend which implements the backend API in the simplest way possible.
    Used in tests of the frontends.

    Handles URIs starting with ``dummy:``.
    """

    def __init__(self, *args, **kwargs):
        super(DummyBackend, self).__init__(*args, **kwargs)

        self.current_playlist = core.CurrentPlaylistController(backend=self)

        library_provider = DummyLibraryProvider(backend=self)
        self.library = core.LibraryController(backend=self,
            provider=library_provider)

        playback_provider = DummyPlaybackProvider(backend=self)
        self.playback = core.PlaybackController(backend=self,
            provider=playback_provider)

        stored_playlists_provider = DummyStoredPlaylistsProvider(backend=self)
        self.stored_playlists = core.StoredPlaylistsController(backend=self,
            provider=stored_playlists_provider)

        self.uri_schemes = [u'dummy']


class DummyLibraryProvider(base.BaseLibraryProvider):
    def __init__(self, *args, **kwargs):
        super(DummyLibraryProvider, self).__init__(*args, **kwargs)
        self.dummy_library = []

    def find_exact(self, **query):
        return Playlist()

    def lookup(self, uri):
        matches = filter(lambda t: uri == t.uri, self.dummy_library)
        if matches:
            return matches[0]

    def refresh(self, uri=None):
        pass

    def search(self, **query):
        return Playlist()


class DummyPlaybackProvider(base.BasePlaybackProvider):
    def __init__(self, *args, **kwargs):
        super(DummyPlaybackProvider, self).__init__(*args, **kwargs)
        self._volume = None

    def pause(self):
        return True

    def play(self, track):
        """Pass None as track to force failure"""
        return track is not None

    def resume(self):
        return True

    def seek(self, time_position):
        return True

    def stop(self):
        return True

    def get_volume(self):
        return self._volume

    def set_volume(self, volume):
        self._volume = volume


class DummyStoredPlaylistsProvider(base.BaseStoredPlaylistsProvider):
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
            playlist.copy(name=new_name)

    def save(self, playlist):
        self._playlists.append(playlist)
