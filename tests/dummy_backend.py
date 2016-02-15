"""A dummy backend for use in tests.

This backend implements the backend API in the simplest way possible.  It is
used in tests of the frontends.
"""

from __future__ import absolute_import, unicode_literals

import pykka

from mopidy import backend
from mopidy.models import Playlist, Ref, SearchResult


def create_proxy(config=None, audio=None):
    return DummyBackend.start(config=config, audio=audio).proxy()


class DummyBackend(pykka.ThreadingActor, backend.Backend):

    def __init__(self, config, audio):
        super(DummyBackend, self).__init__()

        self.library = DummyLibraryProvider(backend=self)
        if audio:
            self.playback = backend.PlaybackProvider(audio=audio, backend=self)
        else:
            self.playback = DummyPlaybackProvider(audio=audio, backend=self)
        self.playlists = DummyPlaylistsProvider(backend=self)

        self.uri_schemes = ['dummy']


class DummyLibraryProvider(backend.LibraryProvider):
    root_directory = Ref.directory(uri='dummy:/', name='dummy')

    def __init__(self, *args, **kwargs):
        super(DummyLibraryProvider, self).__init__(*args, **kwargs)
        self.dummy_library = []
        self.dummy_get_distinct_result = {}
        self.dummy_browse_result = {}
        self.dummy_find_exact_result = SearchResult()
        self.dummy_search_result = SearchResult()

    def browse(self, path):
        return self.dummy_browse_result.get(path, [])

    def get_distinct(self, field, query=None):
        return self.dummy_get_distinct_result.get(field, set())

    def lookup(self, uri):
        return [t for t in self.dummy_library if uri == t.uri]

    def refresh(self, uri=None):
        pass

    def search(self, query=None, uris=None, exact=False):
        if exact:  # TODO: remove uses of dummy_find_exact_result
            return self.dummy_find_exact_result
        return self.dummy_search_result


class DummyPlaybackProvider(backend.PlaybackProvider):

    def __init__(self, *args, **kwargs):
        super(DummyPlaybackProvider, self).__init__(*args, **kwargs)
        self._uri = None
        self._time_position = 0

    def pause(self):
        return True

    def play(self):
        return self._uri and self._uri != 'dummy:error'

    def change_track(self, track):
        """Pass a track with URI 'dummy:error' to force failure"""
        self._uri = track.uri
        self._time_position = 0
        return True

    def prepare_change(self):
        pass

    def resume(self):
        return True

    def seek(self, time_position):
        self._time_position = time_position
        return True

    def stop(self):
        self._uri = None
        return True

    def get_time_position(self):
        return self._time_position


class DummyPlaylistsProvider(backend.PlaylistsProvider):

    def __init__(self, backend):
        super(DummyPlaylistsProvider, self).__init__(backend)
        self._playlists = []

    def set_dummy_playlists(self, playlists):
        """For tests using the dummy provider through an actor proxy."""
        self._playlists = playlists

    def as_list(self):
        return [
            Ref.playlist(uri=pl.uri, name=pl.name) for pl in self._playlists]

    def get_items(self, uri):
        playlist = self.lookup(uri)
        if playlist is None:
            return
        return [
            Ref.track(uri=t.uri, name=t.name) for t in playlist.tracks]

    def lookup(self, uri):
        for playlist in self._playlists:
            if playlist.uri == uri:
                return playlist

    def refresh(self):
        pass

    def create(self, name):
        playlist = Playlist(name=name, uri='dummy:%s' % name)
        self._playlists.append(playlist)
        return playlist

    def delete(self, uri):
        playlist = self.lookup(uri)
        if playlist:
            self._playlists.remove(playlist)

    def save(self, playlist):
        old_playlist = self.lookup(playlist.uri)

        if old_playlist is not None:
            index = self._playlists.index(old_playlist)
            self._playlists[index] = playlist
        else:
            self._playlists.append(playlist)

        return playlist
