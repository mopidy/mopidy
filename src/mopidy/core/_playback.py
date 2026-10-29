from __future__ import annotations

import logging
import urllib.parse
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING
from warnings import deprecated

from pykka.messages import ProxyCall
from pykka.typing import proxy_method

from mopidy.core import _validation as validation
from mopidy.core._state_storage import PlaybackControllerState
from mopidy.exceptions import CoreError
from mopidy.types import DurationMs, PlaybackState, TracklistId, UriScheme

from ._listener import CoreListener

if TYPE_CHECKING:
    from mopidy.audio import AudioProxy
    from mopidy.backend import BackendProxy
    from mopidy.models import TlTrack, Track
    from mopidy.types import Uri

    from ._actor import Backends, Core

logger = logging.getLogger(__name__)

# Max consecutive stream_error recovery attempts for the same track before
# giving up. Resets to zero as soon as a track starts playing successfully.
MAX_STREAM_ERROR_RETRIES = 3


class PlaybackController:
    """Manages playback state and the currently playing track."""

    def __init__(
        self,
        audio: AudioProxy | None,
        backends: Backends,
        core: Core,
    ) -> None:
        # Valid for the life of the controller.
        # TODO: these should be internal
        self.backends = backends
        self.core = core
        self._audio = audio

        # Valid from a playback command or a stream change until the next one.
        self._state = PlaybackState.STOPPED
        self._current_tl_track: TlTrack | None = None
        self._stream_title: str | None = None

        # Valid from the start of a track change until the stream changes or
        # ends.
        self._pending_tl_track: TlTrack | None = None
        self._pending_state: PlaybackState = PlaybackState.PLAYING
        self._last_position: DurationMs | None = None
        self._previous: bool = False

        # Valid from a seek until the position changes.
        self._pending_position: DurationMs | None = None

        # Valid from the restore of the saved state at startup until the first
        # track plays from the saved position, in the saved playback state.
        self._start_at_position: DurationMs | None = None
        self._start_paused: bool = False

        self._stream_error_count = 0

        if self._audio:
            self._audio.set_about_to_finish_callback(self._on_about_to_finish_callback)

    def _get_backend(self, tl_track: TlTrack | None) -> BackendProxy | None:
        if tl_track is None:
            return None
        uri_scheme = UriScheme(urllib.parse.urlparse(tl_track.track.uri).scheme)
        return self.backends.with_playback.get(uri_scheme, None)

    def get_current_tl_track(self) -> TlTrack | None:
        """Get the currently playing or selected track.

        Returns a [TlTrack][mopidy.models.TlTrack] or `None`.
        """
        return self._current_tl_track

    def _set_current_tl_track(self, value: TlTrack | None) -> None:
        """Set the currently playing or selected track.

        *Internal:* This is only for use by Mopidy's test suite.
        """
        self._current_tl_track = value

    def get_current_track(self) -> Track | None:
        """Get the currently playing or selected track.

        Extracted from [get_current_tl_track][] for convenience.

        Returns a [Track][mopidy.models.Track] or `None`.
        """
        return getattr(self.get_current_tl_track(), "track", None)

    def get_current_tlid(self) -> TracklistId | None:
        """Get the currently playing or selected tracklist ID.

        Extracted from [get_current_tl_track][] for convenience.
        """
        return getattr(self.get_current_tl_track(), "tlid", None)

    def get_stream_title(self) -> str | None:
        """Get the current stream title or `None`."""
        return self._stream_title

    def get_state(self) -> PlaybackState:
        """Get The playback state."""
        return self._state

    @deprecated("Use play(), pause(), resume(), or stop() instead")
    def set_state(self, new_state: PlaybackState) -> None:
        """Change the playback state with a playback command.

        /// warning | Deprecated
        This method is deprecated and will be removed in Mopidy 5.0. Use the
        [`play()`][play], [`pause()`][pause], [`resume()`][resume], and
        [`stop()`][stop] methods instead.
        ///

        This method calls the playback command that gives `new_state`:

        | `new_state` | Current playback state | Command |
        | --- | --- | --- |
        | `STOPPED` | any | [`stop()`][stop] |
        | `PAUSED` | `PLAYING` | [`pause()`][pause] |
        | `PLAYING` | `PAUSED` | [`resume()`][resume] |
        | `PLAYING` | `STOPPED` | [`play()`][play] |

        Other calls change nothing.
        """
        validation.check_choice(new_state, validation.PLAYBACK_STATES)

        old_state = self.get_state()
        if new_state == PlaybackState.STOPPED:
            self.stop()
        elif (old_state, new_state) == (PlaybackState.PLAYING, PlaybackState.PAUSED):
            self.pause()
        elif (old_state, new_state) == (PlaybackState.PAUSED, PlaybackState.PLAYING):
            self.resume()
        elif (old_state, new_state) == (PlaybackState.STOPPED, PlaybackState.PLAYING):
            self.play()

    def _set_state(self, new_state: PlaybackState) -> None:
        """Set the playback state.

        This method only maintains core's playback state and emits
        `playback_state_changed` events. It has no effect on the underlying
        backend or audio layers.

        Possible states and transitions:

        ``` mermaid
        graph LR
            STOPPED -->|play| PLAYING;
            STOPPED -->|pause| PAUSED;
            PLAYING -->|stop| STOPPED;
            PLAYING -->|pause| PAUSED;
            PLAYING -->|play| PLAYING;
            PAUSED -->|resume| PLAYING;
            PAUSED -->|stop| STOPPED;
        ```
        """
        validation.check_choice(new_state, validation.PLAYBACK_STATES)

        (old_state, self._state) = (self.get_state(), new_state)
        logger.debug("Changing state: %s -> %s", old_state, new_state)

        self._trigger_playback_state_changed(old_state, new_state)

    def get_time_position(self) -> DurationMs:
        """Get time position in milliseconds."""
        if self._pending_position is not None:
            return self._pending_position
        backend = self._get_backend(self.get_current_tl_track())
        if not backend:
            return DurationMs(0)
        # TODO: Wrap backend call in error handling.
        return backend.playback.get_time_position().get()

    def _on_end_of_stream(self) -> None:
        self._set_state(PlaybackState.STOPPED)
        ended_tl_track = self._current_tl_track
        position = self.get_time_position()
        self._set_current_tl_track(None)
        self._trigger_track_playback_ended(
            tl_track=ended_tl_track,
            time_position=position,
        )

    def _on_stream_changed(self, _uri: Uri) -> None:
        if self._last_position is None:
            position = self.get_time_position()
        else:
            # This code path handles the stop() case, uri should be none.
            position, self._last_position = self._last_position, None

        # Set the new current track before consume mode removes the ended
        # track from the tracklist.
        ended_tl_track = self._current_tl_track
        pending_tl_track, self._pending_tl_track = self._pending_tl_track, None
        pending_state, self._pending_state = self._pending_state, PlaybackState.PLAYING
        if pending_tl_track:
            self._set_current_tl_track(pending_tl_track)

        if self._pending_position is None:
            self._trigger_track_playback_ended(
                tl_track=ended_tl_track,
                time_position=position,
            )

        self._stream_title = None
        if pending_tl_track:
            if self._pending_position is not None:
                self._seek(self._pending_position)
            paused = pending_state == PlaybackState.PAUSED
            self._set_state(PlaybackState.PAUSED if paused else PlaybackState.PLAYING)
            self._trigger_track_playback_started()
            if paused:
                self._trigger_track_playback_paused()
            if self._pending_position is None:
                seek_ok = False
                if self._start_at_position:
                    seek_ok = self.seek(self._start_at_position)
                    self._start_at_position = None
                if not seek_ok and self._start_paused:
                    self.pause()
                    self._start_paused = False

    def _on_position_changed(self, _position: int) -> None:
        if self._pending_position is not None:
            self._trigger_seeked(self._pending_position)
            self._pending_position = None
            if self._start_paused:
                self._start_paused = False
                self.pause()

    def _on_stream_error(self, error: str) -> None:
        """Handle a GStreamer stream error by retrying the current track.

        Addresses https://github.com/mopidy/mopidy/issues/1542: previously
        a stream error (e.g. the audio sink's connection dying) just stopped
        playback silently, with no attempt to recover and no way for core to
        even distinguish this from a normal stop. This retries the current
        track, which causes the backend to rebuild its output pipeline (and
        thus e.g. re-establish a dropped TCP connection), bounded by
        MAX_STREAM_ERROR_RETRIES to avoid retrying forever against a
        persistently broken track or backend.
        """
        tl_track = self.get_current_tl_track()
        if tl_track is None:
            logger.error("Stream error with no current track, giving up: %s", error)
            return

        self._stream_error_count += 1
        if self._stream_error_count > MAX_STREAM_ERROR_RETRIES:
            logger.error(
                "Stream error, giving up after %d attempts for %s: %s",
                self._stream_error_count - 1,
                tl_track.track.uri,
                error,
            )
            self._stream_error_count = 0
            self.stop()
            return

        logger.warning(
            "Stream error, retrying (%d/%d) for %s: %s",
            self._stream_error_count,
            MAX_STREAM_ERROR_RETRIES,
            tl_track.track.uri,
            error,
        )
        self.play(tlid=tl_track.tlid)

    def _on_about_to_finish_callback(self) -> None:
        """Callback that performs a blocking actor call to the real callback.

        This is passed to audio, which is allowed to call this code from the
        audio thread. We pass execution into the core actor to ensure that
        there is no unsafe access of state in core. This must block until
        we get a response.
        """
        self.core.actor_ref.ask(
            ProxyCall(
                attr_path=("playback", "_on_about_to_finish"),
                args=(),
                kwargs={},
            ),
        )

    def _on_about_to_finish(self) -> None:
        if self._state == PlaybackState.STOPPED:
            return

        # Unless overridden by other calls (e.g. next / previous / stop) this
        # will be the last position recorded until the track gets reassigned.
        if self._current_tl_track is not None:
            if self._current_tl_track.track.length is not None:
                self._last_position = DurationMs(self._current_tl_track.track.length)
            else:
                self._last_position = None
        else:
            # TODO: Check if case when track.length isn't populated needs to be
            # handled.
            pass

        self._try_until_playable(
            pending=self.core.tracklist.eot_track(self._current_tl_track),  # ty: ignore[deprecated]
            change=self._change_eot_track,
            step=self.core.tracklist.eot_track,  # ty: ignore[deprecated]
        )

    def _change_eot_track(self, tl_track: TlTrack | None) -> bool:
        """Give the backend the track to play after the current track.

        Returns `False` if the track is not playable.
        """
        if tl_track is None:
            return True
        backend = self._get_backend(tl_track)
        if not backend:
            return False
        try:
            if not backend.playback.change_track(tl_track.track).get():
                return False
        except Exception:
            logger.exception(
                "%s backend caused an exception.",
                backend.actor_ref.actor_class.__name__,
            )
            return False
        self._pending_tl_track = tl_track
        self._pending_state = PlaybackState.PLAYING
        return True

    def _on_tracklist_change(self) -> None:
        """Tell the playback controller that the current playlist has changed.

        Used by [TracklistController][mopidy.core.TracklistController].
        """
        if not self.core.tracklist.get_tl_tracks():
            self.stop()
            self._set_current_tl_track(None)

    def _on_current_track_removed(self, *, next_tl_track: TlTrack | None) -> None:
        """Tell the playback controller that the current track is removed.

        Used by [TracklistController][mopidy.core.TracklistController] when
        other tracks stay in the tracklist.

        Args:
            next_tl_track: The track to change to. `None` stops playback.
        """
        if self.get_state() == PlaybackState.STOPPED:
            self._set_current_tl_track(None)
        else:
            self._change_to_playable(
                pending=next_tl_track,
                step=self.core.tracklist.next_track,  # ty: ignore[deprecated]
            )

    def next(self) -> None:
        """Change to the next track.

        The current playback state will be kept. If it was playing, playing
        will continue. If it was paused, it will still be paused, etc.
        """
        current = self._pending_tl_track or self._current_tl_track
        if current:
            self._change_to_playable(
                pending=self.core.tracklist.next_track(current),  # ty: ignore[deprecated]
                step=self.core.tracklist.next_track,  # ty: ignore[deprecated]
            )

        # TODO: return result?

    def pause(self) -> None:
        """Pause playback."""
        backend = self._get_backend(self.get_current_tl_track())
        # TODO: Wrap backend call in error handling.
        if not backend or backend.playback.pause().get():
            self._set_state(PlaybackState.PAUSED)
            self._trigger_track_playback_paused()

    def play(
        self,
        tlid: TracklistId | None = None,
    ) -> None:
        """Play a track from the tracklist, specified by the tracklist ID.

        Note that the track must already be in the tracklist.

        If no tracklist ID is provided, resume playback of the currently
        active track.

        Args:
            tlid: Tracklist ID of the track to play.
        """
        if tlid is None and self.get_state() == PlaybackState.PAUSED:
            self.resume()
            return

        tl_track: TlTrack | None = None
        if tlid is not None:
            validation.check_integer(tlid, min=1)
            for candidate_tl_track in self.core.tracklist.get_tl_tracks():
                if candidate_tl_track.tlid == tlid:
                    tl_track = candidate_tl_track
                    break
            else:
                logger.info(
                    "Tried to play track with TLID %d, "
                    "but it was not found in the tracklist.",
                    tlid,
                )

        current = self._pending_tl_track or self._current_tl_track
        self._try_until_playable(
            pending=tl_track or current or self.core.tracklist.next_track(None),  # ty: ignore[deprecated]
            change=lambda candidate: (
                candidate is None
                or self._change(tl_track=candidate, state=PlaybackState.PLAYING)
            ),
            step=self.core.tracklist.next_track,  # ty: ignore[deprecated]
        )

    def previous(self) -> None:
        """Change to the previous track.

        The current playback state will be kept. If it was playing, playing
        will continue. If it was paused, it will still be paused, etc.
        """
        self._previous = True
        current = self._pending_tl_track or self._current_tl_track
        if current:
            self._change_to_playable(
                pending=self.core.tracklist.previous_track(current),  # ty: ignore[deprecated]
                step=self.core.tracklist.previous_track,  # ty: ignore[deprecated]
            )

        # TODO: no return value?

    def resume(self) -> None:
        """If paused, resume playing the current track."""
        if self.get_state() != PlaybackState.PAUSED:
            return
        backend = self._get_backend(self.get_current_tl_track())
        # TODO: Wrap backend call in error handling.
        if backend and backend.playback.resume().get():
            self._set_state(PlaybackState.PLAYING)
            # TODO: trigger via gst messages
            self._trigger_track_playback_resumed()

    def seek(self, time_position: DurationMs) -> bool:
        """Seeks to time position given in milliseconds.

        Returns `True` if successful, else `False`.

        Args:
            time_position: Time position in milliseconds.
        """
        # TODO: seek needs to take pending tracks into account :(
        validation.check_integer(time_position)

        if time_position < 0:
            logger.debug("Client seeked to negative position. Seeking to zero.")
            time_position = DurationMs(0)

        if not self.core.tracklist.get_length():
            return False

        if self.get_state() == PlaybackState.STOPPED:
            self.play()

        # We need to prefer the still playing track, but if nothing is playing
        # we fall back to the pending one.
        tl_track = self._current_tl_track or self._pending_tl_track
        if tl_track is None or tl_track.track.length is None:
            return False

        if time_position < 0:
            time_position = DurationMs(0)
        elif time_position > tl_track.track.length:
            # TODO: GStreamer will trigger a about-to-finish for us, use that?
            self.next()
            return True

        # Store our target position.
        self._pending_position = time_position

        # Make sure we switch back to previous track if we get a seek while we
        # have a pending track.
        if self._current_tl_track and self._pending_tl_track:
            return self._change(tl_track=self._current_tl_track, state=self.get_state())

        # TODO: Avoid returning False here when STOPPED (seek is deferred)?
        return self._seek(time_position)

    def _seek(self, time_position: DurationMs) -> bool:
        backend = self._get_backend(self.get_current_tl_track())
        if not backend:
            return False
        # TODO: Wrap backend call in error handling.
        return backend.playback.seek(time_position).get()

    def stop(self) -> None:
        """Stop playing."""
        if self.get_state() != PlaybackState.STOPPED:
            self._last_position = self.get_time_position()
            backend = self._get_backend(self.get_current_tl_track())
            # TODO: Wrap backend call in error handling.
            if not backend or backend.playback.stop().get():
                self._set_state(PlaybackState.STOPPED)

    def _change(  # noqa: PLR0911
        self,
        *,
        tl_track: TlTrack | None,
        state: PlaybackState,
    ) -> bool:
        self._pending_tl_track = tl_track
        self._pending_state = state

        if not tl_track:
            self.stop()
            self._on_end_of_stream()  # pretend an EOS happened for cleanup
            return True

        backend = self._get_backend(tl_track)
        if not backend:
            return False

        # This must happen before prepare_change gets called, otherwise the
        # backend flushes the information of the track.
        self._last_position = self.get_time_position()

        # TODO: Wrap backend call in error handling.
        backend.playback.prepare_change()

        try:
            if not backend.playback.change_track(tl_track.track).get():
                return False
        except Exception:
            logger.exception(
                "%s backend caused an exception.",
                backend.actor_ref.actor_class.__name__,
            )
            return False

        # TODO: Wrap backend calls in error handling.
        if state == PlaybackState.PLAYING:
            try:
                return backend.playback.play().get()
            except TypeError:
                # TODO: check by binding against underlying play method using
                # inspect and otherwise re-raise?
                logger.error(
                    "%s needs to be updated to work with this version of Mopidy.",
                    backend,
                )
                return False
        elif state == PlaybackState.PAUSED:
            return backend.playback.pause().get()
        elif state == PlaybackState.STOPPED:
            # TODO: emit some event now?
            self._current_tl_track = self._pending_tl_track
            self._pending_tl_track = None
            return True

        msg = f"Unknown playback state: {state}"
        raise CoreError(msg)

    def _change_to_playable(
        self,
        *,
        pending: TlTrack | None,
        step: Callable[[TlTrack | None], TlTrack | None],
    ) -> None:
        """Change to the first playable track from `pending`.

        The playback state does not change.

        Args:
            pending: The first track to try.
            step: Gives the track to try after an unplayable track.
        """
        state = self.get_state()
        self._try_until_playable(
            pending=pending,
            change=lambda tl_track: self._change(tl_track=tl_track, state=state),
            step=step,
        )

    def _try_until_playable(
        self,
        *,
        pending: TlTrack | None,
        change: Callable[[TlTrack | None], bool],
        step: Callable[[TlTrack | None], TlTrack | None],
    ) -> None:
        """Call `change` with each track from `pending` until it returns `True`.

        Args:
            pending: The first track to try.
            change: Changes to the given track. Returns `False` if the track
                is not playable.
            step: Gives the track to try after an unplayable track.
        """
        # If no track is playable, the loop can continue with no end, for
        # example in repeat mode, so it stops after a limit. In random mode,
        # the first round has only the tracks that did not play yet, so the
        # limit is two rounds. Then the loop tries each track.
        count = self.core.tracklist.get_length() * 2

        while not change(pending):
            self.core.tracklist._mark_unplayable(pending)
            pending = step(pending)
            count -= 1
            if not count:
                logger.info("No playable track in the list.")
                break

        # In consume mode, remove the unplayable tracks after the loop, so that
        # step() can find the position of each unplayable track.
        self.core.tracklist._remove_unplayable()

    def _trigger_track_playback_paused(self) -> None:
        logger.debug("Triggering track playback paused event")
        if self.get_current_tl_track() is None:
            return
        CoreListener.send(
            "track_playback_paused",
            tl_track=self.get_current_tl_track(),
            time_position=self.get_time_position(),
        )

    def _trigger_track_playback_resumed(self) -> None:
        logger.debug("Triggering track playback resumed event")
        if self.get_current_tl_track() is None:
            return
        CoreListener.send(
            "track_playback_resumed",
            tl_track=self.get_current_tl_track(),
            time_position=self.get_time_position(),
        )

    def _trigger_track_playback_started(self) -> None:
        if self.get_current_tl_track() is None:
            return

        self._stream_error_count = 0

        logger.debug("Triggering track playback started event")
        tl_track = self.get_current_tl_track()
        if tl_track is None:
            return
        self.core.tracklist._mark_playing(tl_track)
        self.core.history._add_track(tl_track.track)
        CoreListener.send("track_playback_started", tl_track=tl_track)

    def _trigger_track_playback_ended(
        self,
        *,
        tl_track: TlTrack | None,
        time_position: int,
    ) -> None:
        if tl_track is None:
            return

        logger.debug("Triggering track playback ended event")

        if not self._previous:
            self.core.tracklist._mark_played(tl_track)
        self._previous = False

        # TODO: Use the lowest of track duration and position.
        CoreListener.send(
            "track_playback_ended",
            tl_track=tl_track,
            time_position=time_position,
        )

    def _trigger_playback_state_changed(
        self,
        old_state: PlaybackState,
        new_state: PlaybackState,
    ) -> None:
        logger.debug("Triggering playback state change event")
        CoreListener.send(
            "playback_state_changed",
            old_state=old_state,
            new_state=new_state,
        )

    def _trigger_seeked(self, time_position: int) -> None:
        # TODO: Trigger this from audio events?
        logger.debug("Triggering seeked event")
        CoreListener.send("seeked", time_position=time_position)

    def _save_state(self) -> PlaybackControllerState:
        return PlaybackControllerState(
            tlid=self.get_current_tlid(),
            time_position=self.get_time_position(),
            state=self.get_state(),
        )

    def _load_state(
        self, state: PlaybackControllerState, coverage: Iterable[str]
    ) -> None:
        if state and "play-last" in coverage and state.tlid is not None:
            if state.state == PlaybackState.PAUSED:
                self._start_paused = True
            if state.state in (PlaybackState.PLAYING, PlaybackState.PAUSED):
                self._start_at_position = DurationMs(state.time_position)
                self.play(tlid=TracklistId(state.tlid))


class PlaybackControllerProxy:
    get_current_tl_track = proxy_method(PlaybackController.get_current_tl_track)
    get_current_track = proxy_method(PlaybackController.get_current_track)
    get_current_tlid = proxy_method(PlaybackController.get_current_tlid)
    get_stream_title = proxy_method(PlaybackController.get_stream_title)
    get_state = proxy_method(PlaybackController.get_state)
    set_state = proxy_method(PlaybackController.set_state)  # ty: ignore[deprecated]
    get_time_position = proxy_method(PlaybackController.get_time_position)
    next = proxy_method(PlaybackController.next)
    pause = proxy_method(PlaybackController.pause)
    play = proxy_method(PlaybackController.play)
    previous = proxy_method(PlaybackController.previous)
    resume = proxy_method(PlaybackController.resume)
    seek = proxy_method(PlaybackController.seek)
    stop = proxy_method(PlaybackController.stop)
