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
            return self.create_explore_playlist(uri, True)
        elif 'soundcloud:user-liked' in uri:
            return self.create_user_liked_playlist(True)
        elif 'soundcloud:user-stream' in uri:
            return self.create_user_stream_playlist(True)
        else:
            return []

    def lookup(self, uri):
        for playlist in self._playlists:
            if playlist.uri == uri:
                # Special case with sets, which already contain all data
                if 'soundcloud:set-' in uri:
                    return playlist
                logger.debug('Resolving with %s', playlist.name)
                return self.lookup_get_tracks(uri)

    def create_explore_playlist(self, uri, streamable=False):
        uri = uri.replace('soundcloud:exp-', '')
        (category, section) = uri.split(';')
        logger.debug('Fetching Explore playlist %s from SoundCloud' % section)
        return Playlist(
            uri='soundcloud:exp-%s' % uri,
            name='Explore %s on SoundCloud' % section,
            tracks=self.backend.sc_api.get_explore_category(
                category, section) if streamable else []
        )

    def create_user_liked_playlist(self, streamable=False):
        username = self.backend.sc_api.get_user().get('username')
        logger.debug('Fetching Liked playlist for %s' % username)
        return Playlist(
            uri='soundcloud:user-liked',
            name="%s's liked on SoundCloud" % username,
            tracks=self.backend.sc_api.get_user_favorites() if streamable else []
        )

    def create_user_stream_playlist(self, streamable=False):
        username = self.backend.sc_api.get_user().get('username')
        logger.debug('Fetching Stream playlist for %s' % username)
        return Playlist(
            uri='soundcloud:user-stream',
            name="%s's stream on SoundCloud" % username,
            tracks=self.backend.sc_api.get_user_stream() if streamable else []
        )

    def refresh(self):
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
        logger.info('Loaded %d SoundCloud playlist(s)', len(self._playlists))
        listener.BackendListener.send('playlists_loaded')

    def save(self, playlist):
        pass  # TODO
