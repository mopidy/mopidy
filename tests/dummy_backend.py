"""A dummy backend for use in tests.

This backend implements the backend API in the simplest way possible.  It is
used in tests of the frontends.
"""

from __future__ import unicode_literals

import pykka

from mopidy import backend
from mopidy.models import Playlist, Ref, SearchResult


def create_dummy_backend_proxy(config=None, audio=None):
    return DummyBackend.start(config=config, audio=audio).proxy()


class DummyBackend(pykka.ThreadingActor, backend.Backend):
    def __init__(self, config, audio):
        super(DummyBackend, self).__init__()

        self.library = DummyLibraryProvider(backend=self)
        self.playback = DummyPlaybackProvider(audio=audio, backend=self)
        self.playlists = DummyPlaylistsProvider(backend=self)

        self.uri_schemes = ['dummy']


class DummyLibraryProvider(backend.LibraryProvider):
    root_directory = Ref.directory(uri='dummy:/', name='dummy')

    def __init__(self, *args, **kwargs):
        super(DummyLibraryProvider, self).__init__(*args, **kwargs)
        self.dummy_library = []
        self.dummy_browse_result = {}
        self.dummy_find_exact_result = SearchResult()
        self.dummy_search_result = SearchResult()

    def browse(self, path):
        return self.dummy_browse_result.get(path, [])

    def find_exact(self, **query):
        return self.dummy_find_exact_result

    def lookup(self, uri):
        return filter(lambda t: uri == t.uri, self.dummy_library)

    def refresh(self, uri=None):
        pass

    def search(self, **query):
        return self.dummy_search_result


class DummyPlaybackProvider(backend.PlaybackProvider):
    def __init__(self, *args, **kwargs):
        super(DummyPlaybackProvider, self).__init__(*args, **kwargs)
        self._time_position = 0

    def pause(self):
        return True

    def play(self, track):
        """Pass a track with URI 'dummy:error' to force failure"""
        self._time_position = 0
        return track.uri != 'dummy:error'

    def resume(self):
        return True

    def seek(self, time_position):
        self._time_position = time_position
        return True

    def stop(self):
        return True

    def get_time_position(self):
        return self._time_position


class DummyPlaylistsProvider(backend.PlaylistsProvider):
    def create(self, name):
        playlist = Playlist(name=name, uri='dummy:%s' % name)
        self._playlists.append(playlist)
        return playlist

    def delete(self, uri):
        playlist = self.lookup(uri)
        if playlist:
            self._playlists.remove(playlist)

    def lookup(self, uri):
        for playlist in self._playlists:
            if playlist.uri == uri:
                return playlist

    def refresh(self):
        pass

    def save(self, playlist):
        old_playlist = self.lookup(playlist.uri)

        if old_playlist is not None:
            index = self._playlists.index(old_playlist)
            self._playlists[index] = playlist
        else:
            self._playlists.append(playlist)

        return playlist
