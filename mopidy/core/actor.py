from __future__ import unicode_literals

import itertools

import pykka

from mopidy.audio import AudioListener, PlaybackState

from .library import LibraryController
from .playback import PlaybackController
from .stored_playlists import StoredPlaylistsController
from .tracklist import TracklistController


class Core(pykka.ThreadingActor, AudioListener):
    #: The library controller. An instance of
    # :class:`mopidy.core.LibraryController`.
    library = None

    #: The playback controller. An instance of
    #: :class:`mopidy.core.PlaybackController`.
    playback = None

    #: The stored playlists controller. An instance of
    #: :class:`mopidy.core.StoredPlaylistsController`.
    stored_playlists = None

    #: The tracklist controller. An instance of
    #: :class:`mopidy.core.TracklistController`.
    tracklist = None

    def __init__(self, audio=None, backends=None):
        super(Core, self).__init__()

        self.backends = Backends(backends)

        self.library = LibraryController(backends=self.backends, core=self)

        self.playback = PlaybackController(
            audio=audio, backends=self.backends, core=self)

        self.stored_playlists = StoredPlaylistsController(
            backends=self.backends, core=self)

        self.tracklist = TracklistController(core=self)

    @property
    def uri_schemes(self):
        """List of URI schemes we can handle"""
        futures = [b.uri_schemes for b in self.backends]
        results = pykka.get_all(futures)
        uri_schemes = itertools.chain(*results)
        return sorted(uri_schemes)

    def reached_end_of_stream(self):
        self.playback.on_end_of_track()

    def state_changed(self, old_state, new_state):
        # XXX: This is a temporary fix for issue #232 while we wait for a more
        # permanent solution with the implementation of issue #234.
        if (new_state == PlaybackState.PAUSED
                and self.playback.state != PlaybackState.PAUSED):
            self.playback.state = new_state
            self.playback._trigger_track_playback_paused()


class Backends(list):
    def __init__(self, backends):
        super(Backends, self).__init__(backends)

        # These lists keeps the backends in the original order, but only
        # includes those which implements the required backend provider. Since
        # it is important to keep the order, we can't simply use .values() on
        # the X_by_uri_scheme dicts below.
        self.with_library = [b for b in backends if b.has_library().get()]
        self.with_playback = [b for b in backends if b.has_playback().get()]
        self.with_stored_playlists = [b for b in backends
            if b.has_stored_playlists().get()]

        self.by_uri_scheme = {}
        for backend in backends:
            for uri_scheme in backend.uri_schemes.get():
                assert uri_scheme not in self.by_uri_scheme, (
                    'Cannot add URI scheme %s for %s, '
                    'it is already handled by %s'
                ) % (
                    uri_scheme, backend.__class__.__name__,
                    self.by_uri_scheme[uri_scheme].__class__.__name__)
                self.by_uri_scheme[uri_scheme] = backend

        self.with_library_by_uri_scheme = {}
        self.with_playback_by_uri_scheme = {}
        self.with_stored_playlists_by_uri_scheme = {}

        for uri_scheme, backend in self.by_uri_scheme.items():
            if backend.has_library().get():
                self.with_library_by_uri_scheme[uri_scheme] = backend
            if backend.has_playback().get():
                self.with_playback_by_uri_scheme[uri_scheme] = backend
            if backend.has_stored_playlists().get():
                self.with_stored_playlists_by_uri_scheme[uri_scheme] = backend
