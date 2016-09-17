from __future__ import absolute_import, unicode_literals

import collections
import itertools
import logging
import os

import pykka

import mopidy

from mopidy import audio, backend, mixer
from mopidy.audio import PlaybackState
from mopidy.core.history import HistoryController
from mopidy.core.library import LibraryController
from mopidy.core.listener import CoreListener
from mopidy.core.mixer import MixerController
from mopidy.core.playback import PlaybackController
from mopidy.core.playlists import PlaylistsController
from mopidy.core.tracklist import TracklistController
from mopidy.internal import path, storage, validation, versioning
from mopidy.internal.deprecation import deprecated_property
from mopidy.internal.models import CoreState


logger = logging.getLogger(__name__)


class Core(
        pykka.ThreadingActor, audio.AudioListener, backend.BackendListener,
        mixer.MixerListener):

    library = None
    """An instance of :class:`~mopidy.core.LibraryController`"""

    history = None
    """An instance of :class:`~mopidy.core.HistoryController`"""

    mixer = None
    """An instance of :class:`~mopidy.core.MixerController`"""

    playback = None
    """An instance of :class:`~mopidy.core.PlaybackController`"""

    playlists = None
    """An instance of :class:`~mopidy.core.PlaylistsController`"""

    tracklist = None
    """An instance of :class:`~mopidy.core.TracklistController`"""

    def __init__(self, config=None, mixer=None, backends=None, audio=None):
        super(Core, self).__init__()

        self._config = config

        self.backends = Backends(backends)

        self.library = LibraryController(backends=self.backends, core=self)
        self.history = HistoryController()
        self.mixer = MixerController(mixer=mixer)
        self.playback = PlaybackController(
            audio=audio, backends=self.backends, core=self)
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
    .. deprecated:: 1.0
        Use :meth:`get_uri_schemes` instead.
    """

    def get_version(self):
        """Get version of the Mopidy core API"""
        return versioning.get_version()

    version = deprecated_property(get_version)
    """
    .. deprecated:: 1.0
        Use :meth:`get_version` instead.
    """

    def reached_end_of_stream(self):
        self.playback._on_end_of_stream()

    def stream_changed(self, uri):
        self.playback._on_stream_changed(uri)

    def position_changed(self, position):
        self.playback._on_position_changed(position)

    def state_changed(self, old_state, new_state, target_state):
        # XXX: This is a temporary fix for issue #232 while we wait for a more
        # permanent solution with the implementation of issue #234. When the
        # Spotify play token is lost, the Spotify backend pauses audio
        # playback, but mopidy.core doesn't know this, so we need to update
        # mopidy.core's state to match the actual state in mopidy.audio. If we
        # don't do this, clients will think that we're still playing.

        # We ignore cases when target state is set as this is buffering
        # updates (at least for now) and we need to get #234 fixed...
        if (new_state == PlaybackState.PAUSED and not target_state and
                self.playback.state != PlaybackState.PAUSED):
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
        if not self.audio or 'title' not in tags:
            return

        tags = self.audio.get_current_tags().get()
        if not tags:
            return

        # TODO: this limits us to only streams that set organization, this is
        # a hack to make sure we don't emit stream title changes for plain
        # tracks. We need a better way to decide if something is a stream.
        if 'title' in tags and tags['title'] and 'organization' in tags:
            title = tags['title'][0]
            self.playback._stream_title = title
            CoreListener.send('stream_title_changed', title=title)

    def setup(self):
        """Do not call this function. It is for internal use at startup."""
        try:
            coverage = []
            if self._config and 'restore_state' in self._config['core']:
                if self._config['core']['restore_state']:
                    coverage = ['tracklist', 'mode', 'play-last', 'mixer',
                                'history']
            if len(coverage):
                self._load_state(coverage)
        except Exception as e:
            logger.warn('Restore state: Unexpected error: %s', str(e))

    def teardown(self):
        """Do not call this function. It is for internal use at shutdown."""
        try:
            if self._config and 'restore_state' in self._config['core']:
                if self._config['core']['restore_state']:
                    self._save_state()
        except Exception as e:
            logger.warn('Unexpected error while saving state: %s', str(e))

    def _get_data_dir(self):
        # get or create data director for core
        data_dir_path = os.path.join(self._config['core']['data_dir'], b'core')
        path.get_or_create_dir(data_dir_path)
        return data_dir_path

    def _save_state(self):
        """
        Save current state to disk.
        """

        file_name = os.path.join(self._get_data_dir(), b'state.json.gz')
        logger.info('Saving state to %s', file_name)

        data = {}
        data['version'] = mopidy.__version__
        data['state'] = CoreState(
            tracklist=self.tracklist._save_state(),
            history=self.history._save_state(),
            playback=self.playback._save_state(),
            mixer=self.mixer._save_state())
        storage.dump(file_name, data)
        logger.debug('Saving state done')

    def _load_state(self, coverage):
        """
        Restore state from disk.

        Load state from disk and restore it. Parameter ``coverage``
        limits the amount of data to restore. Possible
        values for ``coverage`` (list of one or more of):

            - 'tracklist' fill the tracklist
            - 'mode' set tracklist properties (consume, random, repeat, single)
            - 'play-last' restore play state ('tracklist' also required)
            - 'mixer' set mixer volume and mute state
            - 'history' restore history

        :param coverage: amount of data to restore
        :type coverage: list of strings
        """

        file_name = os.path.join(self._get_data_dir(), b'state.json.gz')
        logger.info('Loading state from %s', file_name)

        data = storage.load(file_name)

        try:
            # Try only once. If something goes wrong, the next start is clean.
            os.remove(file_name)
        except OSError:
            logger.info('Failed to delete %s', file_name)

        if 'state' in data:
            core_state = data['state']
            validation.check_instance(core_state, CoreState)
            self.history._load_state(core_state.history, coverage)
            self.tracklist._load_state(core_state.tracklist, coverage)
            self.mixer._load_state(core_state.mixer, coverage)
            # playback after tracklist
            self.playback._load_state(core_state.playback, coverage)
        logger.debug('Loading state done')


class Backends(list):

    def __init__(self, backends):
        super(Backends, self).__init__(backends)

        self.with_library = collections.OrderedDict()
        self.with_library_browse = collections.OrderedDict()
        self.with_playback = collections.OrderedDict()
        self.with_playlists = collections.OrderedDict()

        backends_by_scheme = {}

        def name(b):
            return b.actor_ref.actor_class.__name__

        for b in backends:
            try:
                has_library = b.has_library().get()
                has_library_browse = b.has_library_browse().get()
                has_playback = b.has_playback().get()
                has_playlists = b.has_playlists().get()
            except Exception:
                self.remove(b)
                logger.exception('Fetching backend info for %s failed',
                                 b.actor_ref.actor_class.__name__)

            for scheme in b.uri_schemes.get():
                assert scheme not in backends_by_scheme, (
                    'Cannot add URI scheme "%s" for %s, '
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
