import itertools

import pykka

from mopidy.audio import AudioListener

from .current_playlist import CurrentPlaylistController
from .library import LibraryController
from .playback import PlaybackController
from .stored_playlists import StoredPlaylistsController


class Core(pykka.ThreadingActor, AudioListener):
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

    def __init__(self, audio=None, backends=None):
        super(Core, self).__init__()

        self.backends = Backends(backends)

        self.current_playlist = CurrentPlaylistController(core=self)

        self.library = LibraryController(backends=self.backends, core=self)

        self.playback = PlaybackController(
            audio=audio, backends=self.backends, core=self)

        self.stored_playlists = StoredPlaylistsController(
            backends=self.backends, core=self)

    @property
    def uri_schemes(self):
        """List of URI schemes we can handle"""
        futures = [b.uri_schemes for b in self.backends]
        results = pykka.get_all(futures)
        uri_schemes = itertools.chain(*results)
        return sorted(uri_schemes)

    def reached_end_of_stream(self):
        self.playback.on_end_of_track()


class Backends(list):
    def __init__(self, backends):
        super(Backends, self).__init__(backends)

        self.by_uri_scheme = {}
        for backend in backends:
            uri_schemes = backend.uri_schemes.get()
            for uri_scheme in uri_schemes:
                assert uri_scheme not in self.by_uri_scheme, (
                    'URI scheme %s is already handled by %s'
                    % (uri_scheme, backend.__class__.__name__))
                self.by_uri_scheme[uri_scheme] = backend
