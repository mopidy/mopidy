from __future__ import unicode_literals

import collections
import itertools

import pykka

from mopidy.audio import AudioListener, PlaybackState
from mopidy.backends.listener import BackendListener

from .library import LibraryController
from .listener import CoreListener
from .playback import PlaybackController
from .playlists import PlaylistsController
from .tracklist import TracklistController


class Core(pykka.ThreadingActor, AudioListener, BackendListener):
    #: The library controller. An instance of
    # :class:`mopidy.core.LibraryController`.
    library = None

    #: The playback controller. An instance of
    #: :class:`mopidy.core.PlaybackController`.
    playback = None

    #: The playlists controller. An instance of
    #: :class:`mopidy.core.PlaylistsController`.
    playlists = None

    #: The tracklist controller. An instance of
    #: :class:`mopidy.core.TracklistController`.
    tracklist = None

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
        self.with_playback = collections.OrderedDict()
        self.with_playlists = collections.OrderedDict()

        for backend in backends:
            has_library = backend.has_library().get()
            has_playback = backend.has_playback().get()
            has_playlists = backend.has_playlists().get()

            for scheme in backend.uri_schemes.get():
                self.add(self.with_library, has_library, scheme, backend)
                self.add(self.with_playback, has_playback, scheme, backend)
                self.add(self.with_playlists, has_playlists, scheme, backend)

    def add(self, registry, supported, uri_scheme, backend):
        if not supported:
            return

        if uri_scheme not in registry:
            registry[uri_scheme] = backend
            return

        get_name = lambda actor: actor.actor_ref.actor_class.__name__
        raise AssertionError(
            'Cannot add URI scheme %s for %s, it is already handled by %s' %
            (uri_scheme, get_name(backend), get_name(registry[uri_scheme])))
