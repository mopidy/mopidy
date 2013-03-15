from __future__ import unicode_literals

import logging

from mopidy import settings
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
        username = settings.SOUNDCLOUD_USERNAME
        playlists = []

        liked = Playlist(
            uri='soundcloud:playlist-liked',
            name="%s's liked on SoundCloud" % username,
            tracks=self.backend.sc_api.get_favorites()
        )
        playlists.append(liked)
        
        stream = Playlist(
            uri='soundcloud:playlist-user',
            name="%s's stream on SoundCloud" % username,
            tracks=self.backend.sc_api.get_user_stream()
        )
        playlists.append(stream)

        for (name, uri, tracks) in self.backend.sc_api.get_sets():
            scset = Playlist(
                uri='soundcloud:%s' % uri,
                name=name,
                tracks=tracks
            )
            playlists.append(scset)

        self._playlists = playlists
        listener.BackendListener.send('playlists_loaded')

    def save(self, playlist):
        pass  # TODO
