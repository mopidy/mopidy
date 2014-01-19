from __future__ import unicode_literals

import collections
import itertools

import pykka

from mopidy import audio, backend
from mopidy.audio import PlaybackState
from mopidy.utils import versioning

from .library import LibraryController
from .listener import CoreListener
from .playback import PlaybackController
from .playlists import PlaylistsController
from .tracklist import TracklistController


class Core(pykka.ThreadingActor, audio.AudioListener, backend.BackendListener):
    library = None
    """The library controller. An instance of
    :class:`mopidy.core.LibraryController`."""

    playback = None
    """The playback controller. An instance of
    :class:`mopidy.core.PlaybackController`."""

    playlists = None
    """The playlists controller. An instance of
    :class:`mopidy.core.PlaylistsController`."""

    tracklist = None
    """The tracklist controller. An instance of
    :class:`mopidy.core.TracklistController`."""

    def __init__(self, audio=None, backends=None):
        super(Core, self).__init__()

        self.backends = Backends(backends)

        self.library = LibraryController(backends=self.backends, core=self)

        self.playback = PlaybackController(
            audio=audio, backends=self.backends, core=self)

        self.playlists = PlaylistsController(
            backends=self.backends, core=self)

        self.tracklist = TracklistController(core=self)

    def get_uri_schemes(self):
        futures = [b.uri_schemes for b in self.backends]
        results = pykka.get_all(futures)
        uri_schemes = itertools.chain(*results)
        return sorted(uri_schemes)

    uri_schemes = property(get_uri_schemes)
    """List of URI schemes we can handle"""

    def get_version(self):
        return versioning.get_version()

    version = property(get_version)
    """Version of the Mopidy core API"""

    def reached_end_of_stream(self):
        self.playback.on_end_of_track()

    def state_changed(self, old_state, new_state):
        # XXX: This is a temporary fix for issue #232 while we wait for a more
        # permanent solution with the implementation of issue #234. When the
        # Spotify play token is lost, the Spotify backend pauses audio
        # playback, but mopidy.core doesn't know this, so we need to update
        # mopidy.core's state to match the actual state in mopidy.audio. If we
        # don't do this, clients will think that we're still playing.
        if (new_state == PlaybackState.PAUSED
                and self.playback.state != PlaybackState.PAUSED):
            self.playback.state = new_state
            self.playback._trigger_track_playback_paused()

    def playlists_loaded(self):
        # Forward event from backend to frontends
        CoreListener.send('playlists_loaded')


class Backends(list):
    def __init__(self, backends):
        super(Backends, self).__init__(backends)

        self.with_library = collections.OrderedDict()
        self.with_library_browse = collections.OrderedDict()
        self.with_playback = collections.OrderedDict()
        self.with_playlists = collections.OrderedDict()

        backends_by_scheme = {}
        name = lambda backend: backend.actor_ref.actor_class.__name__

        for backend in backends:
            has_library = backend.has_library().get()
            has_library_browse = backend.has_library_browse().get()
            has_playback = backend.has_playback().get()
            has_playlists = backend.has_playlists().get()

            for scheme in backend.uri_schemes.get():
                assert scheme not in backends_by_scheme, (
                    'Cannot add URI scheme %s for %s, '
                    'it is already handled by %s'
                ) % (scheme, name(backend), name(backends_by_scheme[scheme]))
                backends_by_scheme[scheme] = backend

                if has_library:
                    self.with_library[scheme] = backend
                if has_library_browse:
                    self.with_library_browse[scheme] = backend
                if has_playback:
                    self.with_playback[scheme] = backend
                if has_playlists:
                    self.with_playlists[scheme] = backend
