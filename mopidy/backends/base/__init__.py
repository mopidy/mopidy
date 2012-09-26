from .library import BaseLibraryProvider
from .playback import BasePlaybackProvider
from .stored_playlists import BaseStoredPlaylistsProvider


class Backend(object):
    #: Actor proxy to an instance of :class:`mopidy.audio.Audio`.
    #:
    #: Should be passed to the backend constructor as the kwarg ``audio``,
    #: which will then set this field.
    audio = None

    #: The library provider. An instance of
    # :class:`mopidy.backends.base.BaseLibraryProvider`.
    library = None

    #: The playback provider. An instance of
    #: :class:`mopidy.backends.base.BasePlaybackProvider`.
    playback = None

    #: The stored playlists provider. An instance of
    #: :class:`mopidy.backends.base.BaseStoredPlaylistsProvider`.
    stored_playlists = None

    #: List of URI schemes this backend can handle.
    uri_schemes = []

    def __init__(self, audio):
        self.audio = audio
