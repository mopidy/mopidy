from pykka.actor import ThreadingActor

from mopidy.backends import base
from mopidy.models import Playlist


class DummyBackend(ThreadingActor, base.Backend):
    """
    A backend which implements the backend API in the simplest way possible.
    Used in tests of the frontends.

    Handles URIs starting with ``dummy:``.
    """

    def __init__(self, audio):
        self.library = DummyLibraryProvider(backend=self)
        self.playback = DummyPlaybackProvider(audio=audio, backend=self)
        self.stored_playlists = DummyStoredPlaylistsProvider(backend=self)

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
        self._time_position = 0

    def pause(self):
        return True

    def play(self, track):
        """Pass None as track to force failure"""
        self._time_position = 0
        return track is not None

    def resume(self):
        return True

    def seek(self, time_position):
        self._time_position = time_position
        return True

    def stop(self):
        return True

    def get_time_position(self):
        return self._time_position


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
