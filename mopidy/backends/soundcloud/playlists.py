from __future__ import unicode_literals

import logging

from mopidy import settings
from mopidy.backends import base, listener
from mopidy.models import Playlist

logger = logging.getLogger('mopidy.backends.soundcloud.playlists')


class SoundCloudPlaylistsProvider(base.BasePlaylistsProvider):

    def __init__(self, *args, **kwargs):
        super(SoundCloudPlaylistsProvider, self).__init__(*args, **kwargs)
        self._playlists = []
        self.refresh()

    def create(self, name):
        pass  # TODO

    def delete(self, uri):
        pass  # TODO

    def lookup_get_tracks(self, uri):
        # TODO: Figure out why some sort of internal cache is used for retrieving
        # track-list on mobile clients. If you wan't this to work with mobile
        # clients change defaults to streamable=True
        if 'soundcloud:exp-' in uri:
            logger.info('Detected lookup for explore %s' % uri)
            return self.create_explore_playlist(uri, True)
        elif 'soundcloud:u-liked' in uri:
            logger.info('Detected lookup for liked %s' % uri)
            return self.create_user_liked_playlist(True)
        elif 'soundcloud:u-stream' in uri:
            logger.info('Detected lookup for user stream %s' % uri)
            return self.create_user_stream_playlist(True)
        else:
            logger.info('Detected FAILED lookup for %s' % uri)
            return []

    def lookup(self, uri):
        logger.info('Searching for %s in SoundCloud', uri)
        for playlist in self._playlists:
            if playlist.uri == uri:
                # Special case with sets, which already contain all data
                if 'soundcloud:set-' in uri:
                    logger.info('Resolved with %s', playlist.name)
                    return playlist
                logger.info('Resolving with %s', playlist.name)
                return self.lookup_get_tracks(uri)

    def create_explore_playlist(self, uri, streamable=False):
        uri = uri.replace('soundcloud:exp-', '')
        (category, section) = uri.split(';')
        logger.info('Fetching Explore playlist %s from SoundCloud' % section)
        return Playlist(
            uri='soundcloud:exp-%s' % uri,
            name='Explore %s on SoundCloud' % section,
            tracks=self.backend.sc_api.get_explore_category(
                category, section) if streamable else []
        )

    def create_user_liked_playlist(self, streamable=False):
        username = self.backend.sc_api.get_user().get('username')
        logger.info('Fetching Liked playlist for %s' % username)
        return Playlist(
            uri='soundcloud:u-liked',
            name="%s's liked on SoundCloud" % username,
            tracks=self.backend.sc_api.get_user_favorites() if streamable else []
        )

    def create_user_stream_playlist(self, streamable=False):
        username = self.backend.sc_api.get_user().get('username')
        logger.info('Fetching Stream playlist for %s' % username)
        return Playlist(
            uri='soundcloud:u-stream',
            name="%s's stream on SoundCloud" % username,
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
