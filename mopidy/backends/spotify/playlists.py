from __future__ import unicode_literals

from mopidy.backends import base


class SpotifyPlaylistsProvider(base.BasePlaylistsProvider):
    def create(self, name):
        pass  # TODO

    def delete(self, uri):
        pass  # TODO

    def lookup(self, uri):
        for playlist in self._playlists:
            if playlist.uri == uri:
                return playlist

    def refresh(self):
        pass  # TODO

    def save(self, playlist):
        pass  # TODO
