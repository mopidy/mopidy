import logging

import pykka

from mopidy import settings
from mopidy.backends import base

logger = logging.getLogger('mopidy.backends.spotify')


class SpotifyBackend(pykka.ThreadingActor, base.Backend):
    """
    A backend for playing music from the `Spotify <http://www.spotify.com/>`_
    music streaming service. The backend uses the official `libspotify
    <http://developer.spotify.com/en/libspotify/overview/>`_ library and the
    `pyspotify <http://github.com/winjer/pyspotify/>`_ Python bindings for
    libspotify.

    .. note::

        This product uses SPOTIFY(R) CORE but is not endorsed, certified or
        otherwise approved in any way by Spotify. Spotify is the registered
        trade mark of the Spotify Group.

    **Issues:**
    https://github.com/mopidy/mopidy/issues?labels=backend-spotify

    **Dependencies:**

    - libspotify >= 10, < 11 (libspotify10 package from apt.mopidy.com)
    - pyspotify >= 1.5 (python-spotify package from apt.mopidy.com)

    **Settings:**

    - :attr:`mopidy.settings.SPOTIFY_CACHE_PATH`
    - :attr:`mopidy.settings.SPOTIFY_USERNAME`
    - :attr:`mopidy.settings.SPOTIFY_PASSWORD`
    """

    # Imports inside methods are to prevent loading of __init__.py to fail on
    # missing spotify dependencies.

    def __init__(self, audio):
        super(SpotifyBackend, self).__init__()

        from .library import SpotifyLibraryProvider
        from .playback import SpotifyPlaybackProvider
        from .session_manager import SpotifySessionManager
        from .stored_playlists import SpotifyStoredPlaylistsProvider

        self.library = SpotifyLibraryProvider(backend=self)
        self.playback = SpotifyPlaybackProvider(audio=audio, backend=self)
        self.stored_playlists = SpotifyStoredPlaylistsProvider(backend=self)

        self.uri_schemes = [u'spotify']

        # Fail early if settings are not present
        username = settings.SPOTIFY_USERNAME
        password = settings.SPOTIFY_PASSWORD

        self.spotify = SpotifySessionManager(
            username, password, audio=audio, backend_ref=self.actor_ref)

    def on_start(self):
        logger.info(u'Mopidy uses SPOTIFY(R) CORE')
        logger.debug(u'Connecting to Spotify')
        self.spotify.start()

    def on_stop(self):
        self.spotify.logout()
