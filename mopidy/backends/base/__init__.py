from .library import BaseLibraryProvider
from .playback import BasePlaybackProvider
from .stored_playlists import BaseStoredPlaylistsProvider


class Backend(object):
    #: The current playlist controller. An instance of
    #: :class:`mopidy.backends.base.CurrentPlaylistController`.
    current_playlist = None

    #: The library controller. An instance of
    # :class:`mopidy.backends.base.LibraryController`.
    library = None

    #: The playback controller. An instance of
    #: :class:`mopidy.backends.base.PlaybackController`.
    playback = None

    #: The stored playlists controller. An instance of
    #: :class:`mopidy.backends.base.StoredPlaylistsController`.
    stored_playlists = None

    #: List of URI schemes this backend can handle.
    uri_schemes = []
