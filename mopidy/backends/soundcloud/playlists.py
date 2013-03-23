from __future__ import unicode_literals

import logging

from mopidy import settings
from mopidy.backends import base, listener
from mopidy.models import Playlist

logger = logging.getLogger('mopidy.backends.soundcloud.playlists')


class SoundCloudPlaylistsProvider(base.BasePlaylistsProvider):

    def __init__(self, *args, **kwargs):
        super(SoundCloudPlaylistsProvider, self).__init__(*args, **kwargs)
        self.username = self.backend.sc_api.get_user().get('username')
        self._playlists = []
        self.refresh()

    def create(self, name):
        pass  # TODO

    def delete(self, uri):
        pass  # TODO

    def lookup_get_tracks(self, uri):
        # TODO: Figure out why some sort of internal cache is used for retrieving
        # track-list. Until then stream-able is set to TRUE in create_playsits
        # methods
        if 'soundcloud:exp-' in uri:
            return self.create_explore_playlist(uri, True)
        elif 'soundcloud:u-liked' in uri:
            return self.create_liked_playlist(uri, True)
        elif 'soundcloud:u-stream' in uri:
            return self.create_user_stream_playlist(uri, True)
        else:
            return []

    def lookup(self, uri):
        logger.info('Searching for %s in SoundCloud', uri)
        for playlist in self._playlists:
            if playlist.uri == uri:
                logger.info('Resolving with %s', playlist.name)
                return self.lookup_get_tracks(uri)
            else:
                print('strange error', uri, playlist.uri, playlist.uri == uri)

    def create_explore_playlist(self, uri, streamable=True):
        uri = uri.replace('soundcloud:exp-', '')
        (category, section) = uri.split(';')
        logger.info('Fetching Explore playlist %s from SoundCloud' % section)
        return Playlist(
            uri='soundcloud:exp-%s' % uri,
            name='Explore %s on SoundCloud' % section,
            tracks=self.backend.sc_api.get_explore_category(
                category, section) if streamable else []
        )

    def create_user_liked_playlist(self, streamable=True):
        logger.info('Fetching Liked playlist for %s' % self.username)
        return Playlist(
            uri='soundcloud:u-liked',
            name="%s's liked on SoundCloud" % self.username,
            tracks=self.backend.sc_api.get_favorites() if streamable else []
        )

    def create_user_stream_playlist(self, streamable=True):
        logger.info('Fetching Stream playlist for %s' % self.username)
        return Playlist(
            uri='soundcloud:u-stream',
            name="%s's stream on SoundCloud" % self.username,
            tracks=self.backend.sc_api.get_user_stream() if streamable else []
        )

    def refresh(self):
        logger.info('Loading playlists from SoundCloud')

        self._playlists.append(self.create_user_liked_playlist())
        self._playlists.append(self.create_user_stream_playlist())

        for (name, uri, tracks) in self.backend.sc_api.get_sets():
            scset = Playlist(
                uri='soundcloud:set-%s' % uri,
                name=name,
                tracks=tracks
            )
            self._playlists.append(scset)

        for cat in settings.SOUNDCLOUD_EXPLORE:
            exp = self.create_explore_playlist(cat.replace('/', ';'))
            self._playlists.append(exp)
        logger.info('Loaded %d Soundcloud playlist(s)', len(self._playlists))
        listener.BackendListener.send('playlists_loaded')

    def save(self, playlist):
        pass  # TODO
