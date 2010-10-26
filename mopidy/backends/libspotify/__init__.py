import logging

from mopidy import settings
from mopidy.backends.base import (BaseBackend, BaseCurrentPlaylistController,
    BasePlaybackController)

logger = logging.getLogger('mopidy.backends.libspotify')

ENCODING = 'utf-8'

class LibspotifyBackend(BaseBackend):
    """
    A `Spotify <http://www.spotify.com/>`_ backend which uses the official
    `libspotify <http://developer.spotify.com/en/libspotify/overview/>`_
    library and the `pyspotify <http://github.com/winjer/pyspotify/>`_ Python
    bindings for libspotify.

    **Issues:** http://github.com/jodal/mopidy/issues/labels/backend-libspotify

    **Settings:**

    - :attr:`mopidy.settings.SPOTIFY_LIB_CACHE`
    - :attr:`mopidy.settings.SPOTIFY_USERNAME`
    - :attr:`mopidy.settings.SPOTIFY_PASSWORD`

    .. note::

        This product uses SPOTIFY(R) CORE but is not endorsed, certified or
        otherwise approved in any way by Spotify. Spotify is the registered
        trade mark of the Spotify Group.
    """

    # Imports inside methods are to prevent loading of __init__.py to fail on
    # missing spotify dependencies.

    def __init__(self, *args, **kwargs):
        from .library import LibspotifyLibraryController
        from .playback import LibspotifyPlaybackProvider
        from .stored_playlists import LibspotifyStoredPlaylistsController

        super(LibspotifyBackend, self).__init__(*args, **kwargs)

        self.current_playlist = BaseCurrentPlaylistController(backend=self)

        self.library = LibspotifyLibraryController(backend=self)

        playback_provider = LibspotifyPlaybackProvider(backend=self)
        self.playback = BasePlaybackController(backend=self,
            provider=playback_provider)

        self.stored_playlists = LibspotifyStoredPlaylistsController(
            backend=self)

        self.uri_handlers = [u'spotify:', u'http://open.spotify.com/']

        self.spotify = self._connect()

    def _connect(self):
        from .session_manager import LibspotifySessionManager

        logger.info(u'Mopidy uses SPOTIFY(R) CORE')
        logger.debug(u'Connecting to Spotify')
        spotify = LibspotifySessionManager(
            settings.SPOTIFY_USERNAME, settings.SPOTIFY_PASSWORD,
            core_queue=self.core_queue,
            output=self.output)
        spotify.start()
        return spotify
