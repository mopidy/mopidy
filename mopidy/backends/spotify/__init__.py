import logging

from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry

from mopidy import settings
from mopidy.backends.base import (Backend, CurrentPlaylistController,
    LibraryController, PlaybackController, StoredPlaylistsController)
from mopidy.outputs.base import BaseOutput

logger = logging.getLogger('mopidy.backends.spotify')

ENCODING = 'utf-8'

class SpotifyBackend(ThreadingActor, Backend):
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
    http://github.com/mopidy/mopidy/issues/labels/backend-spotify

    **Settings:**

    - :attr:`mopidy.settings.SPOTIFY_CACHE_PATH`
    - :attr:`mopidy.settings.SPOTIFY_USERNAME`
    - :attr:`mopidy.settings.SPOTIFY_PASSWORD`
    """

    # Imports inside methods are to prevent loading of __init__.py to fail on
    # missing spotify dependencies.

    def __init__(self, *args, **kwargs):
        from .library import SpotifyLibraryProvider
        from .playback import SpotifyPlaybackProvider
        from .stored_playlists import SpotifyStoredPlaylistsProvider

        super(SpotifyBackend, self).__init__(*args, **kwargs)

        self.current_playlist = CurrentPlaylistController(backend=self)

        library_provider = SpotifyLibraryProvider(backend=self)
        self.library = LibraryController(backend=self,
            provider=library_provider)

        playback_provider = SpotifyPlaybackProvider(backend=self)
        self.playback = PlaybackController(backend=self,
            provider=playback_provider)

        stored_playlists_provider = SpotifyStoredPlaylistsProvider(
            backend=self)
        self.stored_playlists = StoredPlaylistsController(backend=self,
            provider=stored_playlists_provider)

        self.uri_handlers = [u'spotify:', u'http://open.spotify.com/']

        self.output = None
        self.spotify = None

    def on_start(self):
        output_refs = ActorRegistry.get_by_class(BaseOutput)
        assert len(output_refs) == 1, 'Expected exactly one running output.'
        self.output = output_refs[0].proxy()

        self.spotify = self._connect()

    def _connect(self):
        from .session_manager import SpotifySessionManager

        logger.info(u'Mopidy uses SPOTIFY(R) CORE')
        logger.debug(u'Connecting to Spotify')
        spotify = SpotifySessionManager(
            settings.SPOTIFY_USERNAME, settings.SPOTIFY_PASSWORD)
        spotify.start()
        return spotify
