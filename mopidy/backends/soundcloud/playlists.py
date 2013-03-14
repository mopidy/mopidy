from __future__ import unicode_literals

import logging

from mopidy.backends import base, listener
from mopidy.models import Playlist

logger = logging.getLogger('mopidy.backends.soundcloud.playlists')


class SoundcloudPlaylistsProvider(base.BasePlaylistsProvider):
    def __init__(self, *args, **kwargs):
        super(SoundcloudPlaylistsProvider, self).__init__(*args, **kwargs)
        self.refresh()

    def create(self, name):
        pass  # TODO

    def delete(self, uri):
        pass  # TODO

    def lookup(self, uri):
        for playlist in self._playlists:
            if playlist.uri == uri:
                return playlist

    def refresh(self):
        logger.info('Loading playlists from SoundCloud')

        playlists = []

        playlist = Playlist(
            uri="soundcloud:playlist-liked",
            name="Liked on SoundCloud",
            tracks=self.backend.sc_api.get_favorites()
        )
        playlists.append(playlist)
        
        # TODO Sets, User stream
        
        self._playlists = playlists
        listener.BackendListener.send('playlists_loaded')

    def save(self, playlist):
        pass  # TODO
