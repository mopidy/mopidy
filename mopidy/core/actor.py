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


class Backends(object):
    def __init__(self, backends):
        self._backends = backends

        uri_schemes_by_backend = {
            backend: backend.uri_schemes.get()
            for backend in backends}
        self.by_uri_scheme = {
            uri_scheme: backend
            for backend, uri_schemes in uri_schemes_by_backend.items()
            for uri_scheme in uri_schemes}

    def __len__(self):
        return len(self._backends)

    def __getitem__(self, key):
        return self._backends[key]
