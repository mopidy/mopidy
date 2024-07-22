from __future__ import annotations

import logging
import urllib.parse
from collections.abc import Iterable
from typing import TYPE_CHECKING

from pykka.messages import ProxyCall
from pykka.typing import proxy_method

from mopidy.audio import PlaybackState
from mopidy.core import listener
from mopidy.exceptions import CoreError
from mopidy.internal import models, validation
from mopidy.models import TlTrack
from mopidy.types import DurationMs, TracklistId, UriScheme

if TYPE_CHECKING:
    from mopidy.audio.actor import AudioProxy
    from mopidy.backend import BackendProxy
    from mopidy.core.actor import Backends, Core
    from mopidy.models import Track
    from mopidy.types import Uri

logger = logging.getLogger(__name__)


class PlaybackController:
    def __init__(
        self,
        audio: AudioProxy | None,
        backends: Backends,
        core: Core,
    ) -> None:
        # TODO: these should be internal
        self.backends = backends
        self.core = core
        self._audio = audio

        self._stream_title: str | None = None
        self._state = PlaybackState.STOPPED

        self._current_tl_track: TlTrack | None = None
        self._pending_tl_track: TlTrack | None = None

        self._pending_position: DurationMs | None = None
        self._last_position: DurationMs | None = None
        self._previous: bool = False

        self._start_at_position: DurationMs | None = None
        self._start_paused: bool = False

        if self._audio:
            self._audio.set_about_to_finish_callback(self._on_about_to_finish_callback)

    def _get_backend(self, tl_track: TlTrack | None) -> BackendProxy | None:
        if tl_track is None or tl_track.track.uri is None:
            return None
        uri_scheme = UriScheme(urllib.parse.urlparse(tl_track.track.uri).scheme)
        return self.backends.with_playback.get(uri_scheme, None)

    def get_current_tl_track(self) -> TlTrack | None:
        """Get the currently playing or selected track.

        Returns a :class:`mopidy.models.TlTrack` or :class:`None`.
        """
        return self._current_tl_track

    def _set_current_tl_track(self, value: TlTrack | None) -> None:
        """Set the currently playing or selected track.

        *Internal:* This is only for use by Mopidy's test suite.
        """
        self._current_tl_track = value

    def get_current_track(self) -> Track | None:
        """Get the currently playing or selected track.

        Extracted from :meth:`get_current_tl_track` for convenience.

        Returns a :class:`mopidy.models.Track` or :class:`None`.
        """
        match self.get_current_tl_track():
            case TlTrack(_tlid, track):
                return track
            case None:
                return None

    def get_current_tlid(self) -> TracklistId | None:
        """Get the currently playing or selected tracklist ID.

        Extracted from :meth:`get_current_tl_track` for convenience.

        .. versionadded:: 1.1
        """
        match self.get_current_tl_track():
            case TlTrack(tlid, _track):
                return tlid
            case None:
                return None

    def get_stream_title(self) -> str | None:
        """Get the current stream title or :class:`None`."""
        return self._stream_title

    def get_state(self) -> PlaybackState:
        """Get The playback state."""
        return self._state

    def set_state(self, new_state: PlaybackState) -> None:
        """Set the playback state.

        Must be :attr:`PLAYING`, :attr:`PAUSED`, or :attr:`STOPPED`.

        Possible states and transitions:

        .. digraph:: state_transitions

            "STOPPED" -> "PLAYING" [ label="play" ]
            "STOPPED" -> "PAUSED" [ label="pause" ]
            "PLAYING" -> "STOPPED" [ label="stop" ]
            "PLAYING" -> "PAUSED" [ label="pause" ]
            "PLAYING" -> "PLAYING" [ label="play" ]
            "PAUSED" -> "PLAYING" [ label="resume" ]
            "PAUSED" -> "STOPPED" [ label="stop" ]
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
        self.set_state(PlaybackState.STOPPED)
        if self._current_tl_track:
            self._trigger_track_playback_ended(self.get_time_position())
        self._set_current_tl_track(None)

    def _on_stream_changed(self, _uri: Uri) -> None:
        if self._last_position is None:
            position = self.get_time_position()
        else:
            # This code path handles the stop() case, uri should be none.
            position, self._last_position = self._last_position, None

        if self._pending_position is None:
            self._trigger_track_playback_ended(position)

        self._stream_title = None
        if self._pending_tl_track:
            self._set_current_tl_track(self._pending_tl_track)
            self._pending_tl_track = None

            if self._pending_position is None:
                self.set_state(PlaybackState.PLAYING)
                self._trigger_track_playback_started()
                seek_ok = False
                if self._start_at_position:
                    seek_ok = self.seek(self._start_at_position)
                    self._start_at_position = None
                if not seek_ok and self._start_paused:
                    self.pause()
                    self._start_paused = False
            else:
                self._seek(self._pending_position)
                self.set_state(PlaybackState.PLAYING)
                self._trigger_track_playback_started()

    def _on_position_changed(self, _position: int) -> None:
        if self._pending_position is not None:
            self._trigger_seeked(self._pending_position)
            self._pending_position = None
            if self._start_paused:
                self._start_paused = False
                self.pause()

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
            )
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

        pending = self.core.tracklist.eot_track(self._current_tl_track)
        # avoid endless loop if 'repeat' is 'true' and no track is playable
        # * 2 -> second run to get all playable track in a shuffled playlist
        count = self.core.tracklist.get_length() * 2

        while pending:
            backend = self._get_backend(pending)
            if backend:
                try:
                    if backend.playback.change_track(pending.track).get():
                        self._pending_tl_track = pending
                        break
                except Exception:
                    logger.exception(
                        "%s backend caused an exception.",
                        backend.actor_ref.actor_class.__name__,
                    )

            self.core.tracklist._mark_unplayable(pending)
            pending = self.core.tracklist.eot_track(pending)
            count -= 1
            if not count:
                logger.info("No playable track in the list.")
                break

    def _on_tracklist_change(self) -> None:
        """Tell the playback controller that the current playlist has changed.

        Used by :class:`mopidy.core.TracklistController`.
        """
        tl_tracks = self.core.tracklist.get_tl_tracks()
        if not tl_tracks:
            self.stop()
            self._set_current_tl_track(None)
        elif self.get_current_tl_track() not in tl_tracks:
            self._set_current_tl_track(None)

    def next(self) -> None:
        """Change to the next track.

        The current playback state will be kept. If it was playing, playing
        will continue. If it was paused, it will still be paused, etc.
        """
        state = self.get_state()
        current = self._pending_tl_track or self._current_tl_track
        # avoid endless loop if 'repeat' is 'true' and no track is playable
        # * 2 -> second run to get all playable track in a shuffled playlist
        count = self.core.tracklist.get_length() * 2

        while current:
            pending = self.core.tracklist.next_track(current)
            if self._change(pending, state):
                break
            self.core.tracklist._mark_unplayable(pending)
            current = pending
            count -= 1
            if not count:
                logger.info("No playable track in the list.")
                break

        # TODO return result?

    def pause(self) -> None:
        """Pause playback."""
        backend = self._get_backend(self.get_current_tl_track())
        # TODO: Wrap backend call in error handling.
        if not backend or backend.playback.pause().get():
            self.set_state(PlaybackState.PAUSED)
            self._trigger_track_playback_paused()

    def play(
        self,
        tlid: TracklistId | None = None,
    ) -> None:
        """Play a track from the tracklist, specified by the tracklist ID.

        Note that the track must already be in the tracklist.

        If no tracklist ID is provided, resume playback of the currently
        active track.

        .. versionremoved:: 4.0
            The ``tl_track`` argument. Use ``tlid`` instead.

        :param tlid: Tracklist ID of the track to play
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
        pending = tl_track or current or self.core.tracklist.next_track(None)
        # avoid endless loop if 'repeat' is 'true' and no track is playable
        # * 2 -> second run to get all playable track in a shuffled playlist
        count = self.core.tracklist.get_length() * 2

        while pending:
            if self._change(pending, PlaybackState.PLAYING):
                break
            self.core.tracklist._mark_unplayable(pending)
            current = pending
            pending = self.core.tracklist.next_track(current)
            count -= 1
            if not count:
                logger.info("No playable track in the list.")
                break

    def _change(  # noqa: PLR0911
        self,
        pending_tl_track: TlTrack | None,
        state: PlaybackState,
    ) -> bool:
        self._pending_tl_track = pending_tl_track

        if not pending_tl_track:
            self.stop()
            self._on_end_of_stream()  # pretend an EOS happened for cleanup
            return True

        backend = self._get_backend(pending_tl_track)
        if not backend:
            return False

        # This must happen before prepare_change gets called, otherwise the
        # backend flushes the information of the track.
        self._last_position = self.get_time_position()

        # TODO: Wrap backend call in error handling.
        backend.playback.prepare_change()

        try:
            if not backend.playback.change_track(pending_tl_track.track).get():
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

        raise CoreError(f"Unknown playback state: {state}")

    def previous(self) -> None:
        """Change to the previous track.

        The current playback state will be kept. If it was playing, playing
        will continue. If it was paused, it will still be paused, etc.
        """
        self._previous = True
        state = self.get_state()
        current = self._pending_tl_track or self._current_tl_track
        # avoid endless loop if 'repeat' is 'true' and no track is playable
        # * 2 -> second run to get all playable track in a shuffled playlist
        count = self.core.tracklist.get_length() * 2

        while current:
            pending = self.core.tracklist.previous_track(current)
            if self._change(pending, state):
                break
            self.core.tracklist._mark_unplayable(pending)
            current = pending
            count -= 1
            if not count:
                logger.info("No playable track in the list.")
                break

        # TODO: no return value?

    def resume(self) -> None:
        """If paused, resume playing the current track."""
        if self.get_state() != PlaybackState.PAUSED:
            return
        backend = self._get_backend(self.get_current_tl_track())
        # TODO: Wrap backend call in error handling.
        if backend and backend.playback.resume().get():
            self.set_state(PlaybackState.PLAYING)
            # TODO: trigger via gst messages
            self._trigger_track_playback_resumed()

    def seek(self, time_position: DurationMs) -> bool:
        """Seeks to time position given in milliseconds.

        Returns :class:`True` if successful, else :class:`False`.

        :param time_position: time position in milliseconds
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
            return self._change(self._current_tl_track, self.get_state())

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
                self.set_state(PlaybackState.STOPPED)

    def _trigger_track_playback_paused(self) -> None:
        logger.debug("Triggering track playback paused event")
        if self.get_current_tl_track() is None:
            return
        listener.CoreListener.send(
            "track_playback_paused",
            tl_track=self.get_current_tl_track(),
            time_position=self.get_time_position(),
        )

    def _trigger_track_playback_resumed(self) -> None:
        logger.debug("Triggering track playback resumed event")
        if self.get_current_tl_track() is None:
            return
        listener.CoreListener.send(
            "track_playback_resumed",
            tl_track=self.get_current_tl_track(),
            time_position=self.get_time_position(),
        )

    def _trigger_track_playback_started(self) -> None:
        if self.get_current_tl_track() is None:
            return

        logger.debug("Triggering track playback started event")
        tl_track = self.get_current_tl_track()
        if tl_track is None:
            return
        self.core.tracklist._mark_playing(tl_track)
        self.core.history._add_track(tl_track.track)
        listener.CoreListener.send("track_playback_started", tl_track=tl_track)

    def _trigger_track_playback_ended(self, time_position_before_stop: int) -> None:
        tl_track = self.get_current_tl_track()
        if tl_track is None:
            return

        logger.debug("Triggering track playback ended event")

        if not self._previous:
            self.core.tracklist._mark_played(self._current_tl_track)
        self._previous = False

        # TODO: Use the lowest of track duration and position.
        listener.CoreListener.send(
            "track_playback_ended",
            tl_track=tl_track,
            time_position=time_position_before_stop,
        )

    def _trigger_playback_state_changed(
        self,
        old_state: PlaybackState,
        new_state: PlaybackState,
    ) -> None:
        logger.debug("Triggering playback state change event")
        listener.CoreListener.send(
            "playback_state_changed", old_state=old_state, new_state=new_state
        )

    def _trigger_seeked(self, time_position: int) -> None:
        # TODO: Trigger this from audio events?
        logger.debug("Triggering seeked event")
        listener.CoreListener.send("seeked", time_position=time_position)

    def _save_state(self) -> models.PlaybackState:
        return models.PlaybackState(
            tlid=self.get_current_tlid(),
            time_position=self.get_time_position(),
            state=self.get_state(),
        )

    def _load_state(self, state: models.PlaybackState, coverage: Iterable[str]) -> None:
        if state and "play-last" in coverage and state.tlid is not None:
            if state.state == PlaybackState.PAUSED:
                self._start_paused = True
            if state.state in (PlaybackState.PLAYING, PlaybackState.PAUSED):
                self._start_at_position = DurationMs(state.time_position)
                self.play(tlid=state.tlid)


class PlaybackControllerProxy:
    get_current_tl_track = proxy_method(PlaybackController.get_current_tl_track)
    get_current_track = proxy_method(PlaybackController.get_current_track)
    get_current_tlid = proxy_method(PlaybackController.get_current_tlid)
    get_stream_title = proxy_method(PlaybackController.get_stream_title)
    get_state = proxy_method(PlaybackController.get_state)
    set_state = proxy_method(PlaybackController.set_state)
    get_time_position = proxy_method(PlaybackController.get_time_position)
    next = proxy_method(PlaybackController.next)
    pause = proxy_method(PlaybackController.pause)
    play = proxy_method(PlaybackController.play)
    previous = proxy_method(PlaybackController.previous)
    resume = proxy_method(PlaybackController.resume)
    seek = proxy_method(PlaybackController.seek)
    stop = proxy_method(PlaybackController.stop)
