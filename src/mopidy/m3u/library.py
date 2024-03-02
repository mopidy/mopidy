from mopidy import backend

from . import playlists, translator


class M3ULibraryProvider(backend.LibraryProvider):
    def __init__(self, backend, playlist_provider: playlists.M3UPlaylistsProvider):
        super().__init__(backend)
        self.playlist_provider = playlist_provider

    def lookup(self, uri):
        return translator.refs_to_tracks(self.playlist_provider.get_items(uri))
