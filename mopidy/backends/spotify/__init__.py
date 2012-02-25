import logging

from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry

from mopidy import settings
from mopidy.backends.base import (Backend, CurrentPlaylistController,
    LibraryController, PlaybackController, StoredPlaylistsController)
from mopidy.gstreamer import GStreamer

logger = logging.getLogger('mopidy.backends.spotify')

BITRATES = {96: 2, 160: 0, 320: 1}

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

        self.uri_schemes = [u'spotify']

        self.gstreamer = None
        self.spotify = None

        # Fail early if settings are not present
        self.username = settings.SPOTIFY_USERNAME
        self.password = settings.SPOTIFY_PASSWORD

    def on_start(self):
        gstreamer_refs = ActorRegistry.get_by_class(GStreamer)
        assert len(gstreamer_refs) == 1, \
            'Expected exactly one running GStreamer.'
        self.gstreamer = gstreamer_refs[0].proxy()

        logger.info(u'Mopidy uses SPOTIFY(R) CORE')
        self.spotify = self._connect()

    def on_stop(self):
        self.spotify.logout()

    def _connect(self):
        from .session_manager import SpotifySessionManager

        logger.debug(u'Connecting to Spotify')
        spotify = SpotifySessionManager(self.username, self.password)
        spotify.start()
        return spotify
