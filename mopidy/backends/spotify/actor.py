from __future__ import unicode_literals

import logging

import pykka

from mopidy import settings
from mopidy.backends import base

logger = logging.getLogger('mopidy.backends.spotify')


class SpotifyBackend(pykka.ThreadingActor, base.Backend):
    # Imports inside methods are to prevent loading of __init__.py to fail on
    # missing spotify dependencies.

    def __init__(self, audio):
        super(SpotifyBackend, self).__init__()

        from .library import SpotifyLibraryProvider
        from .playback import SpotifyPlaybackProvider
        from .session_manager import SpotifySessionManager
        from .playlists import SpotifyPlaylistsProvider

        self.library = SpotifyLibraryProvider(backend=self)
        self.playback = SpotifyPlaybackProvider(audio=audio, backend=self)
        self.playlists = SpotifyPlaylistsProvider(backend=self)

        self.uri_schemes = ['spotify']

        # Fail early if settings are not present
        username = settings.SPOTIFY_USERNAME
        password = settings.SPOTIFY_PASSWORD
        proxy = settings.SPOTIFY_PROXY_HOST
        proxy_username = settings.SPOTIFY_PROXY_USERNAME
        proxy_password = settings.SPOTIFY_PROXY_PASSWORD

        self.spotify = SpotifySessionManager(
            username, password, audio=audio, backend_ref=self.actor_ref,
            proxy=proxy, proxy_username=proxy_username,
            proxy_password=proxy_password)

    def on_start(self):
        logger.info('Mopidy uses SPOTIFY(R) CORE')
        logger.debug('Connecting to Spotify')
        self.spotify.start()

    def on_stop(self):
        self.spotify.logout()
