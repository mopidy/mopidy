# ruff: noqa: ARG002

from __future__ import annotations

import itertools
import logging
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

import pykka
from pykka.typing import ActorMemberMixin, proxy_method

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
from mopidy.internal import path, storage
from mopidy.internal.models import CoreState, StoredState

if TYPE_CHECKING:
    from mopidy.config import Config
    from mopidy.core.history import HistoryControllerProxy
    from mopidy.core.library import LibraryControllerProxy
    from mopidy.core.mixer import MixerControllerProxy
    from mopidy.core.playback import PlaybackControllerProxy
    from mopidy.core.playlists import PlaylistsControllerProxy
    from mopidy.core.tracklist import TracklistControllerProxy
    from mopidy.types import Uri

logger = logging.getLogger(__name__)


class Core(
    pykka.ThreadingActor,
    audio.AudioListener,
    backend.BackendListener,
    mixer.MixerListener,
):
    library: LibraryController
    """An instance of :class:`~mopidy.core.LibraryController`"""

    history: HistoryController
    """An instance of :class:`~mopidy.core.HistoryController`"""

    mixer: MixerController
    """An instance of :class:`~mopidy.core.MixerController`"""

    playback: PlaybackController
    """An instance of :class:`~mopidy.core.PlaybackController`"""

    playlists: PlaylistsController
    """An instance of :class:`~mopidy.core.PlaylistsController`"""

    tracklist: TracklistController
    """An instance of :class:`~mopidy.core.TracklistController`"""

    def __init__(
        self,
        config: Config,
        *,
        mixer: mixer.MixerProxy | None = None,
        backends: Iterable[backend.BackendProxy],
        audio: audio.AudioProxy | None = None,
    ) -> None:
        super().__init__()

        self._config = config

        self.backends = Backends(backends or [])

        self.library = pykka.traversable(
            LibraryController(backends=self.backends, core=self)
        )
        self.history = pykka.traversable(HistoryController())
        self.mixer = pykka.traversable(MixerController(mixer=mixer))
        self.playback = pykka.traversable(
            PlaybackController(audio=audio, backends=self.backends, core=self)
        )
        self.playlists = pykka.traversable(
            PlaylistsController(backends=self.backends, core=self)
        )
        self.tracklist = pykka.traversable(TracklistController(core=self))

        self.audio = audio

    def get_uri_schemes(self) -> list[backend.UriScheme]:
        """Get list of URI schemes we can handle."""
        futures = [b.uri_schemes for b in self.backends]
        results = pykka.get_all(futures)
        uri_schemes = itertools.chain(*results)
        return sorted(uri_schemes)

    def get_version(self) -> str:
        """Get version of the Mopidy core API."""
        return mopidy.__version__

    def reached_end_of_stream(self) -> None:
        self.playback._on_end_of_stream()

    def stream_changed(self, uri: Uri) -> None:
        self.playback._on_stream_changed(uri)

    def position_changed(self, position: int) -> None:
        self.playback._on_position_changed(position)

    def state_changed(
        self,
        old_state: PlaybackState,
        new_state: PlaybackState,
        target_state: PlaybackState | None,
    ) -> None:
        # XXX: This is a temporary fix for issue #232 while we wait for a more
        # permanent solution with the implementation of issue #234. When the
        # Spotify play token is lost, the Spotify backend pauses audio
        # playback, but mopidy.core doesn't know this, so we need to update
        # mopidy.core's state to match the actual state in mopidy.audio. If we
        # don't do this, clients will think that we're still playing.

        # We ignore cases when target state is set as this is buffering
        # updates (at least for now) and we need to get #234 fixed...
        if (
            new_state == PlaybackState.PAUSED
            and not target_state
            and self.playback.get_state() != PlaybackState.PAUSED
        ):
            self.playback.set_state(new_state)
            self.playback._trigger_track_playback_paused()

    def playlists_loaded(self) -> None:
        # Forward event from backend to frontends
        CoreListener.send("playlists_loaded")

    def volume_changed(self, volume: int) -> None:
        # Forward event from mixer to frontends
        CoreListener.send("volume_changed", volume=volume)

    def mute_changed(self, mute: bool) -> None:
        # Forward event from mixer to frontends
        CoreListener.send("mute_changed", mute=mute)

    def tags_changed(self, tags: set[str]) -> None:
        if not self.audio or "title" not in tags:
            return

        current_tags = self.audio.get_current_tags().get()
        if not current_tags:
            return

        self.playback._stream_title = None
        # TODO: Do not emit stream title changes for plain tracks. We need a
        # better way to decide if something is a stream.
        if current_tags.get("title"):
            title = current_tags["title"][0]
            current_track = self.playback.get_current_track()
            if current_track is not None and current_track.name != title:
                self.playback._stream_title = title
                CoreListener.send("stream_title_changed", title=title)

    def _setup(self) -> None:
        """Do not call this function. It is for internal use at startup."""
        try:
            coverage = []
            if (
                self._config
                and "restore_state" in self._config["core"]
                and self._config["core"]["restore_state"]
            ):
                coverage = [
                    "tracklist",
                    "mode",
                    "play-last",
                    "mixer",
                    "history",
                ]
            if len(coverage):
                self._load_state(coverage)
        except Exception as e:
            logger.warning("Restore state: Unexpected error: %s", str(e))

    def _teardown(self) -> None:
        """Do not call this function. It is for internal use at shutdown."""
        try:
            if (
                self._config
                and "restore_state" in self._config["core"]
                and self._config["core"]["restore_state"]
            ):
                self._save_state()
        except Exception as e:
            logger.warning("Unexpected error while saving state: %s", str(e))

    def _get_data_dir(self) -> Path:
        # get or create data director for core
        data_dir_path = path.expand_path(self._config["core"]["data_dir"]) / "core"
        path.get_or_create_dir(data_dir_path)
        return data_dir_path

    def _get_state_file(self) -> Path:
        return self._get_data_dir() / "state.json.gz"

    def _save_state(self) -> None:
        """Save current state to disk."""
        state_file = self._get_state_file()
        logger.info("Saving state to %s", state_file)

        data = StoredState(
            version=mopidy.__version__,
            state=CoreState(
                tracklist=self.tracklist._save_state(),
                history=self.history._save_state(),
                playback=self.playback._save_state(),
                mixer=self.mixer._save_state(),
            ),
        )
        storage.dump(state_file, data)
        logger.debug("Saving state done")

    def _load_state(self, coverage: Iterable[str]) -> None:
        """Restore state from disk.

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
        state_file = self._get_state_file()
        logger.info("Loading state from %s", state_file)

        data = storage.load(state_file)

        try:
            # Try only once. If something goes wrong, the next start is clean.
            state_file.unlink()
        except OSError:
            logger.info("Failed to delete %s", state_file)

        if data is not None:
            self.history._load_state(data.state.history, coverage)
            self.tracklist._load_state(data.state.tracklist, coverage)
            self.mixer._load_state(data.state.mixer, coverage)
            # playback after tracklist
            self.playback._load_state(data.state.playback, coverage)
        logger.debug("Loading state done")


class Backends(list):
    def __init__(self, backends: Iterable[backend.BackendProxy]) -> None:
        super().__init__(backends)

        self.with_library: dict[backend.UriScheme, backend.BackendProxy] = {}
        self.with_library_browse: dict[backend.UriScheme, backend.BackendProxy] = {}
        self.with_playback: dict[backend.UriScheme, backend.BackendProxy] = {}
        self.with_playlists: dict[backend.UriScheme, backend.BackendProxy] = {}

        backends_by_scheme: dict[backend.UriScheme, backend.BackendProxy] = {}

        def name(backend_proxy: backend.BackendProxy) -> str:
            return backend_proxy.actor_ref.actor_class.__name__

        for b in backends:
            try:
                has_library = b.has_library().get()
                has_library_browse = b.has_library_browse().get()
                has_playback = b.has_playback().get()
                has_playlists = b.has_playlists().get()
            except Exception:
                self.remove(b)
                logger.exception("Fetching backend info for %s failed", name(b))
                continue

            for scheme in b.uri_schemes.get():
                if scheme in backends_by_scheme:
                    raise AssertionError(
                        f"Cannot add URI scheme {scheme!r} for {name(b)}, "
                        f"it is already handled by {name(backends_by_scheme[scheme])}"
                    )
                backends_by_scheme[scheme] = b

                if has_library:
                    self.with_library[scheme] = b
                if has_library_browse:
                    self.with_library_browse[scheme] = b
                if has_playback:
                    self.with_playback[scheme] = b
                if has_playlists:
                    self.with_playlists[scheme] = b


class CoreProxy(ActorMemberMixin, pykka.ActorProxy[Core]):
    library: LibraryControllerProxy
    history: HistoryControllerProxy
    mixer: MixerControllerProxy
    playback: PlaybackControllerProxy
    playlists: PlaylistsControllerProxy
    tracklist: TracklistControllerProxy
    get_uri_schemes = proxy_method(Core.get_uri_schemes)
    get_version = proxy_method(Core.get_version)
    reached_end_of_stream = proxy_method(Core.reached_end_of_stream)
    stream_changed = proxy_method(Core.stream_changed)
    position_changed = proxy_method(Core.position_changed)
    state_changed = proxy_method(Core.state_changed)
    playlists_loaded = proxy_method(Core.playlists_loaded)
    volume_changed = proxy_method(Core.volume_changed)
    mute_changed = proxy_method(Core.mute_changed)
    tags_changed = proxy_method(Core.tags_changed)
