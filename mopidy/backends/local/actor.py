import logging

from pykka.actor import ThreadingActor

from mopidy.backends import base

from .library import LocalLibraryProvider
from .stored_playlists import LocalStoredPlaylistsProvider

logger = logging.getLogger(u'mopidy.backends.local')


class LocalBackend(ThreadingActor, base.Backend):
    """
    A backend for playing music from a local music archive.

    **Dependencies:**

    - None

    **Settings:**

    - :attr:`mopidy.settings.LOCAL_MUSIC_PATH`
    - :attr:`mopidy.settings.LOCAL_PLAYLIST_PATH`
    - :attr:`mopidy.settings.LOCAL_TAG_CACHE_FILE`
    """

    def __init__(self, audio):
        self.library = LocalLibraryProvider(backend=self)
        self.playback = base.BasePlaybackProvider(audio=audio, backend=self)
        self.stored_playlists = LocalStoredPlaylistsProvider(backend=self)

        self.uri_schemes = [u'file']
