from __future__ import unicode_literals

import logging

import pykka

from mopidy.backends import base
from mopidy.backends.spotify.library import SpotifyLibraryProvider
from mopidy.backends.spotify.playback import SpotifyPlaybackProvider
from mopidy.backends.spotify.session_manager import SpotifySessionManager
from mopidy.backends.spotify.playlists import SpotifyPlaylistsProvider

logger = logging.getLogger('mopidy.backends.spotify')


class SpotifyBackend(pykka.ThreadingActor, base.Backend):
    def __init__(self, config, audio):
        super(SpotifyBackend, self).__init__()

        self.config = config

        self.library = SpotifyLibraryProvider(backend=self)
        self.playback = SpotifyPlaybackProvider(audio=audio, backend=self)
        self.playlists = SpotifyPlaylistsProvider(backend=self)

        self.uri_schemes = ['spotify']

        self.spotify = SpotifySessionManager(
            config, audio=audio, backend_ref=self.actor_ref)

    def on_start(self):
        logger.info('Mopidy uses SPOTIFY(R) CORE')
        logger.debug('Connecting to Spotify')
        self.spotify.start()

    def on_stop(self):
        self.spotify.logout()
