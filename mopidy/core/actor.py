from __future__ import absolute_import, unicode_literals

import collections
import itertools

import pykka

from mopidy import audio, backend, mixer
from mopidy.audio import PlaybackState
from mopidy.audio.utils import convert_tags_to_track
from mopidy.core.history import HistoryController
from mopidy.core.library import LibraryController
from mopidy.core.listener import CoreListener
from mopidy.core.mixer import MixerController
from mopidy.core.playback import PlaybackController
from mopidy.core.playlists import PlaylistsController
from mopidy.core.tracklist import TracklistController
from mopidy.models import TlTrack, Track
from mopidy.utils import versioning
from mopidy.utils.deprecation import deprecated_property


class Core(
        pykka.ThreadingActor, audio.AudioListener, backend.BackendListener,
        mixer.MixerListener):

    library = None
    """The library controller. An instance of
    :class:`mopidy.core.LibraryController`."""

    history = None
    """The playback history controller. An instance of
    :class:`mopidy.core.HistoryController`."""

    mixer = None
    """The mixer controller. An instance of
    :class:`mopidy.core.MixerController`."""

    playback = None
    """The playback controller. An instance of
    :class:`mopidy.core.PlaybackController`."""

    playlists = None
    """The playlists controller. An instance of
    :class:`mopidy.core.PlaylistsController`."""

    tracklist = None
    """The tracklist controller. An instance of
    :class:`mopidy.core.TracklistController`."""

    def __init__(self, mixer=None, backends=None, audio=None):
        super(Core, self).__init__()

        self.backends = Backends(backends)

        self.library = LibraryController(backends=self.backends, core=self)
        self.history = HistoryController()
        self.mixer = MixerController(mixer=mixer)
        self.playback = PlaybackController(backends=self.backends, core=self)
        self.playlists = PlaylistsController(backends=self.backends, core=self)
        self.tracklist = TracklistController(core=self)

        self.audio = audio

    def get_uri_schemes(self):
        """Get list of URI schemes we can handle"""
        futures = [b.uri_schemes for b in self.backends]
        results = pykka.get_all(futures)
        uri_schemes = itertools.chain(*results)
        return sorted(uri_schemes)

    uri_schemes = deprecated_property(get_uri_schemes)
    """
    .. deprecated:: 0.20
        Use :meth:`get_uri_schemes` instead.
    """

    def get_version(self):
        """Get version of the Mopidy core API"""
        return versioning.get_version()

    version = deprecated_property(get_version)
    """
    .. deprecated:: 0.20
        Use :meth:`get_version` instead.
    """

    def reached_end_of_stream(self):
        self.playback.on_end_of_track()

    def state_changed(self, old_state, new_state, target_state):
        # XXX: This is a temporary fix for issue #232 while we wait for a more
        # permanent solution with the implementation of issue #234. When the
        # Spotify play token is lost, the Spotify backend pauses audio
        # playback, but mopidy.core doesn't know this, so we need to update
        # mopidy.core's state to match the actual state in mopidy.audio. If we
        # don't do this, clients will think that we're still playing.

        # We ignore cases when target state is set as this is buffering
        # updates (at least for now) and we need to get #234 fixed...
        if (new_state == PlaybackState.PAUSED and not target_state
                and self.playback.state != PlaybackState.PAUSED):
            self.playback.state = new_state
            self.playback._trigger_track_playback_paused()

    def playlists_loaded(self):
        # Forward event from backend to frontends
        CoreListener.send('playlists_loaded')

    def volume_changed(self, volume):
        # Forward event from mixer to frontends
        CoreListener.send('volume_changed', volume=volume)

    def mute_changed(self, mute):
        # Forward event from mixer to frontends
        CoreListener.send('mute_changed', mute=mute)

    def tags_changed(self, tags):
        if not self.audio:
            return

        current_tl_track = self.playback.get_current_tl_track()
        if current_tl_track is None:
            return

        tags = self.audio.get_current_tags().get()
        if not tags:
            return

        current_track = current_tl_track.track
        tags_track = convert_tags_to_track(tags)

        track_kwargs = {k: v for k, v in current_track.__dict__.items() if v}
        track_kwargs.update(
            {k: v for k, v in tags_track.__dict__.items() if v})

        self.playback._current_metadata_track = TlTrack(**{
            'tlid': current_tl_track.tlid,
            'track': Track(**track_kwargs)})

        # TODO Move this into playback.current_metadata_track setter?
        CoreListener.send('current_metadata_changed')


class Backends(list):
    def __init__(self, backends):
        super(Backends, self).__init__(backends)

        self.with_library = collections.OrderedDict()
        self.with_library_browse = collections.OrderedDict()
        self.with_playback = collections.OrderedDict()
        self.with_playlists = collections.OrderedDict()

        backends_by_scheme = {}
        name = lambda b: b.actor_ref.actor_class.__name__

        for b in backends:
            has_library = b.has_library().get()
            has_library_browse = b.has_library_browse().get()
            has_playback = b.has_playback().get()
            has_playlists = b.has_playlists().get()

            for scheme in b.uri_schemes.get():
                assert scheme not in backends_by_scheme, (
                    'Cannot add URI scheme %s for %s, '
                    'it is already handled by %s'
                ) % (scheme, name(b), name(backends_by_scheme[scheme]))
                backends_by_scheme[scheme] = b

                if has_library:
                    self.with_library[scheme] = b
                if has_library_browse:
                    self.with_library_browse[scheme] = b
                if has_playback:
                    self.with_playback[scheme] = b
                if has_playlists:
                    self.with_playlists[scheme] = b
