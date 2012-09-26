from pykka.actor import ThreadingActor

from .current_playlist import CurrentPlaylistController
from .library import LibraryController
from .playback import PlaybackController
from .stored_playlists import StoredPlaylistsController


class Core(ThreadingActor):
    #: The current playlist controller. An instance of
    #: :class:`mopidy.core.CurrentPlaylistController`.
    current_playlist = None

    #: The library controller. An instance of
    # :class:`mopidy.core.LibraryController`.
    library = None

    #: The playback controller. An instance of
    #: :class:`mopidy.core.PlaybackController`.
    playback = None

    #: The stored playlists controller. An instance of
    #: :class:`mopidy.core.StoredPlaylistsController`.
    stored_playlists = None

    def __init__(self, audio=None, backend=None):
        self._backend = backend

        self.current_playlist = CurrentPlaylistController(core=self)

        self.library = LibraryController(backend=backend, core=self)

        self.playback = PlaybackController(
            audio=audio, backend=backend, core=self)

        self.stored_playlists = StoredPlaylistsController(
            backend=backend, core=self)

    @property
    def uri_schemes(self):
        """List of URI schemes we can handle"""
        return self._backend.uri_schemes.get()
