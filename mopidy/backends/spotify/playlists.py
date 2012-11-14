from __future__ import unicode_literals

from mopidy.backends import base


class SpotifyPlaylistsProvider(base.BasePlaylistsProvider):
    def create(self, name):
        pass  # TODO

    def delete(self, uri):
        pass  # TODO

    def lookup(self, uri):
        pass  # TODO

    def refresh(self):
        pass  # TODO

    def save(self, playlist):
        pass  # TODO
