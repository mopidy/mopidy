import logging

from mopidy import settings
from mopidy.backends.base import BaseBackend, BaseCurrentPlaylistController

logger = logging.getLogger('mopidy.backends.libspotify')

ENCODING = 'utf-8'

class LibspotifyBackend(BaseBackend):
    """
    A Spotify backend which uses the official `libspotify library
    <http://developer.spotify.com/en/libspotify/overview/>`_.

    `pyspotify <http://github.com/winjer/pyspotify/>`_ is the Python bindings
    for libspotify. It got no documentation, but multiple examples are
    available. Like libspotify, pyspotify's calls are mostly asynchronous.

    **Issues:** http://github.com/jodal/mopidy/issues/labels/backend-libspotify
    """

    # Imports inside methods are to prevent loading of __init__.py to fail on
    # missing spotify dependencies.

    def __init__(self, *args, **kwargs):
        from .library import LibspotifyLibraryController
        from .playback import LibspotifyPlaybackController
        from .stored_playlists import LibspotifyStoredPlaylistsController

        super(LibspotifyBackend, self).__init__(*args, **kwargs)

        self.current_playlist = BaseCurrentPlaylistController(backend=self)
        self.library = LibspotifyLibraryController(backend=self)
        self.playback = LibspotifyPlaybackController(backend=self)
        self.stored_playlists = LibspotifyStoredPlaylistsController(
            backend=self)
        self.uri_handlers = [u'spotify:', u'http://open.spotify.com/']
        self.spotify = self._connect()

    def _connect(self):
        from .session_manager import LibspotifySessionManager

        logger.info(u'Connecting to Spotify')
        spotify = LibspotifySessionManager(
            settings.SPOTIFY_USERNAME, settings.SPOTIFY_PASSWORD,
            core_queue=self.core_queue,
            output_queue=self.output_queue)
        spotify.start()
        return spotify
