from __future__ import annotations

import logging
import random
from collections.abc import Iterable
from typing import TYPE_CHECKING

from pykka.typing import proxy_method

from mopidy import exceptions
from mopidy.core import listener
from mopidy.internal import deprecation, validation
from mopidy.internal.models import TracklistState
from mopidy.models import TlTrack, Track
from mopidy.types import TracklistId

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from mopidy.core.actor import Core
    from mopidy.types import Query, TracklistField, Uri


class TracklistController:
    def __init__(self, core: Core) -> None:
        self.core = core
        self._next_tlid: TracklistId = TracklistId(1)
        self._tl_tracks: list[TlTrack] = []
        self._version: int = 0

        self._consume: bool = False
        self._random: bool = False
        self._shuffled: list[TlTrack] = []
        self._repeat: bool = False
        self._single: bool = False

    def get_tl_tracks(self) -> list[TlTrack]:
        """Get tracklist as list of :class:`mopidy.models.TlTrack`."""
        return self._tl_tracks[:]

    def get_tracks(self) -> list[Track]:
        """Get tracklist as list of :class:`mopidy.models.Track`."""
        return [tl_track.track for tl_track in self._tl_tracks]

    def get_length(self) -> int:
        """Get length of the tracklist."""
        return len(self._tl_tracks)

    def get_version(self) -> int:
        """Get the tracklist version.

        Integer which is increased every time the tracklist is changed. Is not
        reset before Mopidy is restarted.
        """
        return self._version

    def _increase_version(self) -> None:
        self._version += 1
        self.core.playback._on_tracklist_change()
        self._trigger_tracklist_changed()

    def get_consume(self) -> bool:
        """Get consume mode.

        :class:`True`
            Tracks are removed from the tracklist when they have been played.
        :class:`False`
            Tracks are not removed from the tracklist.
        """
        return self._consume

    def set_consume(self, value: bool) -> None:
        """Set consume mode.

        :class:`True`
            Tracks are removed from the tracklist when they have been played.
        :class:`False`
            Tracks are not removed from the tracklist.
        """
        validation.check_boolean(value)
        if self.get_consume() != value:
            self._trigger_options_changed()
        self._consume = value

    def get_random(self) -> bool:
        """Get random mode.

        :class:`True`
            Tracks are selected at random from the tracklist.
        :class:`False`
            Tracks are played in the order of the tracklist.
        """
        return self._random

    def set_random(self, value: bool) -> None:
        """Set random mode.

        :class:`True`
            Tracks are selected at random from the tracklist.
        :class:`False`
            Tracks are played in the order of the tracklist.
        """
        validation.check_boolean(value)
        if self.get_random() != value:
            self._trigger_options_changed()
        if value:
            self._shuffled = self.get_tl_tracks()
            random.shuffle(self._shuffled)
        self._random = value

    def get_repeat(self) -> bool:
        """Get repeat mode.

        :class:`True`
            The tracklist is played repeatedly.
        :class:`False`
            The tracklist is played once.
        """
        return self._repeat

    def set_repeat(self, value: bool) -> None:
        """Set repeat mode.

        To repeat a single track, set both ``repeat`` and ``single``.

        :class:`True`
            The tracklist is played repeatedly.
        :class:`False`
            The tracklist is played once.
        """
        validation.check_boolean(value)
        if self.get_repeat() != value:
            self._trigger_options_changed()
        self._repeat = value

    def get_single(self) -> bool:
        """Get single mode.

        :class:`True`
            Playback is stopped after current song, unless in ``repeat`` mode.
        :class:`False`
            Playback continues after current song.
        """
        return self._single

    def set_single(self, value: bool) -> None:
        """Set single mode.

        :class:`True`
            Playback is stopped after current song, unless in ``repeat`` mode.
        :class:`False`
            Playback continues after current song.
        """
        validation.check_boolean(value)
        if self.get_single() != value:
            self._trigger_options_changed()
        self._single = value

    def index(
        self,
        tl_track: TlTrack | None = None,
        tlid: int | None = None,
    ) -> int | None:
        """The position of the given track in the tracklist.

        If neither *tl_track* or *tlid* is given we return the index of
        the currently playing track.

        :param tl_track: the track to find the index of
        :param tlid: TLID of the track to find the index of

        .. versionadded:: 1.1
            The *tlid* parameter
        """
        if tl_track is not None:
            validation.check_instance(tl_track, TlTrack)
        if tlid is not None:
            validation.check_integer(tlid, min=1)

        if tl_track is None and tlid is None:
            tl_track = self.core.playback.get_current_tl_track()

        if tl_track is not None:
            try:
                return self._tl_tracks.index(tl_track)
            except ValueError:
                pass
        elif tlid is not None:
            for i, tl_track in enumerate(self._tl_tracks):
                if tl_track.tlid == tlid:
                    return i
        return None

    def get_eot_tlid(self) -> int | None:
        """The TLID of the track that will be played after the current track.

        Not necessarily the same TLID as returned by :meth:`get_next_tlid`.

        .. versionadded:: 1.1
        """
        current_tl_track = self.core.playback.get_current_tl_track()

        with deprecation.ignore("core.tracklist.eot_track"):
            eot_tl_track = self.eot_track(current_tl_track)

        return getattr(eot_tl_track, "tlid", None)

    def eot_track(self, tl_track: TlTrack | None) -> TlTrack | None:
        """The track that will be played after the given track.

        Not necessarily the same track as :meth:`next_track`.

        .. deprecated:: 3.0
            Use :meth:`get_eot_tlid` instead.

        :param tl_track: the reference track
        """
        deprecation.warn("core.tracklist.eot_track")
        if tl_track is not None:
            validation.check_instance(tl_track, TlTrack)
        if self.get_single() and self.get_repeat():
            return tl_track
        if self.get_single():
            return None

        # Current difference between next and EOT handling is that EOT needs to
        # handle "single", with that out of the way the rest of the logic is
        # shared.
        return self.next_track(tl_track)

    def get_next_tlid(self) -> int | None:
        """The tlid of the track that will be played if calling
        :meth:`mopidy.core.PlaybackController.next()`.

        For normal playback this is the next track in the tracklist. If repeat
        is enabled the next track can loop around the tracklist. When random is
        enabled this should be a random track, all tracks should be played once
        before the tracklist repeats.

        .. versionadded:: 1.1
        """
        current_tl_track = self.core.playback.get_current_tl_track()

        with deprecation.ignore("core.tracklist.next_track"):
            next_tl_track = self.next_track(current_tl_track)

        return getattr(next_tl_track, "tlid", None)

    def next_track(self, tl_track: TlTrack | None) -> TlTrack | None:
        """The track that will be played if calling
        :meth:`mopidy.core.PlaybackController.next()`.

        For normal playback this is the next track in the tracklist. If repeat
        is enabled the next track can loop around the tracklist. When random is
        enabled this should be a random track, all tracks should be played once
        before the tracklist repeats.

        .. deprecated:: 3.0
            Use :meth:`get_next_tlid` instead.

        :param tl_track: the reference track
        """
        deprecation.warn("core.tracklist.next_track")
        if tl_track is not None:
            validation.check_instance(tl_track, TlTrack)

        if not self._tl_tracks:
            return None

        if (
            self.get_random()
            and not self._shuffled
            and (self.get_repeat() or not tl_track)
        ):
            logger.debug("Shuffling tracks")
            self._shuffled = self._tl_tracks[:]
            random.shuffle(self._shuffled)

        if self.get_random():
            if self._shuffled:
                return self._shuffled[0]
            return None

        next_index = self.index(tl_track)
        if next_index is None:
            next_index = 0
        else:
            next_index += 1

        if self.get_repeat():
            if self.get_consume() and len(self._tl_tracks) == 1:
                return None
            next_index %= len(self._tl_tracks)
        elif next_index >= len(self._tl_tracks):
            return None

        return self._tl_tracks[next_index]

    def get_previous_tlid(self) -> int | None:
        """Returns the TLID of the track that will be played if calling
        :meth:`mopidy.core.PlaybackController.previous()`.

        For normal playback this is the previous track in the tracklist. If
        random and/or consume is enabled it should return the current track
        instead.

        .. versionadded:: 1.1
        """
        current_tl_track = self.core.playback.get_current_tl_track()

        with deprecation.ignore("core.tracklist.previous_track"):
            previous_tl_track = self.previous_track(current_tl_track)

        return getattr(previous_tl_track, "tlid", None)

    def previous_track(self, tl_track: TlTrack | None) -> TlTrack | None:
        """Returns the track that will be played if calling
        :meth:`mopidy.core.PlaybackController.previous()`.

        For normal playback this is the previous track in the tracklist. If
        random and/or consume is enabled it should return the current track
        instead.

        .. deprecated:: 3.0
            Use :meth:`get_previous_tlid` instead.

        :param tl_track: the reference track
        """
        deprecation.warn("core.tracklist.previous_track")
        if tl_track is not None:
            validation.check_instance(tl_track, TlTrack)

        if self.get_repeat() or self.get_consume() or self.get_random():
            return tl_track

        position = self.index(tl_track)

        if position in (None, 0):
            return None

        # Since we know we are not at zero we have to be somewhere in the range
        # 1 - len(tracks) Thus 'position - 1' will always be within the list.
        return self._tl_tracks[position - 1]

    def add(  # noqa: C901
        self,
        tracks: Iterable[Track] | None = None,
        at_position: int | None = None,
        uris: Iterable[Uri] | None = None,
    ) -> list[TlTrack]:
        """Add tracks to the tracklist.

        If ``uris`` is given instead of ``tracks``, the URIs are
        looked up in the library and the resulting tracks are added to the
        tracklist.

        If ``at_position`` is given, the tracks are inserted at the given
        position in the tracklist. If ``at_position`` is not given, the tracks
        are appended to the end of the tracklist.

        Triggers the :meth:`mopidy.core.CoreListener.tracklist_changed` event.

        :param tracks: tracks to add
        :param at_position: position in tracklist to add tracks
        :param uris: list of URIs for tracks to add

        .. versionadded:: 1.0
            The ``uris`` argument.

        .. deprecated:: 1.0
            The ``tracks`` argument. Use ``uris``.
        """
        if sum(o is not None for o in [tracks, uris]) != 1:
            raise ValueError('Exactly one of "tracks" or "uris" must be set')

        if tracks is not None:
            validation.check_instances(tracks, Track)
        if uris is not None:
            validation.check_uris(uris)
        validation.check_integer(at_position or 0)

        if tracks:
            deprecation.warn("core.tracklist.add:tracks_arg")

        if tracks is None:
            tracks = []
            assert uris is not None
            track_map = self.core.library.lookup(uris=uris)
            for uri in uris:
                tracks.extend(track_map[uri])

        tl_tracks = []
        max_length = self.core._config["core"]["max_tracklist_length"]

        for track in tracks:
            if self.get_length() >= max_length:
                raise exceptions.TracklistFull(
                    f"Tracklist may contain at most {max_length:d} tracks."
                )

            tl_track = TlTrack(self._next_tlid, track)
            self._next_tlid = TracklistId(self._next_tlid + 1)
            if at_position is not None:
                self._tl_tracks.insert(at_position, tl_track)
                at_position += 1
            else:
                self._tl_tracks.append(tl_track)
            tl_tracks.append(tl_track)

        if tl_tracks:
            self._increase_version()

        return tl_tracks

    def clear(self) -> None:
        """Clear the tracklist.

        Triggers the :meth:`mopidy.core.CoreListener.tracklist_changed` event.
        """
        self._tl_tracks = []
        self._increase_version()

    def filter(self, criteria: Query[TracklistField]) -> list[TlTrack]:
        """Filter the tracklist by the given criteria.

        Each rule in the criteria consists of a model field and a list of
        values to compare it against. If the model field matches any of the
        values, it may be returned.

        Only tracks that match all the given criteria are returned.

        Examples::

            # Returns tracks with TLIDs 1, 2, 3, or 4 (tracklist ID)
            filter({'tlid': [1, 2, 3, 4]})

            # Returns track with URIs 'xyz' or 'abc'
            filter({'uri': ['xyz', 'abc']})

            # Returns track with a matching TLIDs (1, 3 or 6) and a
            # matching URI ('xyz' or 'abc')
            filter({'tlid': [1, 3, 6], 'uri': ['xyz', 'abc']})

        :param criteria: one or more rules to match by
        """
        tlids = criteria.pop("tlid", [])
        validation.check_query(criteria, validation.TRACKLIST_FIELDS.keys())
        validation.check_instances(tlids, int)

        matches = self._tl_tracks
        for key, values in criteria.items():
            matches = [ct for ct in matches if getattr(ct.track, key) in values]
        if tlids:
            matches = [ct for ct in matches if ct.tlid in tlids]
        return matches

    def move(self, start: int, end: int, to_position: int) -> None:
        """Move the tracks in the slice ``[start:end]`` to ``to_position``.

        Triggers the :meth:`mopidy.core.CoreListener.tracklist_changed` event.

        :param start: position of first track to move
        :param end: position after last track to move
        :param to_position: new position for the tracks
        """
        if start == end:
            end += 1

        tl_tracks = self._tl_tracks

        # TODO: use validation helpers?
        if start >= end:
            raise AssertionError("start must be smaller than end")
        if start < 0:
            raise AssertionError("start must be at least zero")
        if end > len(tl_tracks):
            raise AssertionError("end can not be larger than tracklist length")
        if to_position < 0:
            raise AssertionError("to_position must be at least zero")
        if to_position > len(tl_tracks):
            raise AssertionError("to_position can not be larger than tracklist length")

        new_tl_tracks = tl_tracks[:start] + tl_tracks[end:]
        for tl_track in tl_tracks[start:end]:
            new_tl_tracks.insert(to_position, tl_track)
            to_position += 1
        self._tl_tracks = new_tl_tracks
        self._increase_version()

    def remove(self, criteria: Query[TracklistField]) -> list[TlTrack]:
        """Remove the matching tracks from the tracklist.

        Uses :meth:`filter()` to lookup the tracks to remove.

        Triggers the :meth:`mopidy.core.CoreListener.tracklist_changed` event.

        Returns the removed tracks.

        :param criteria: one or more rules to match by
        """
        tl_tracks = self.filter(criteria)
        for tl_track in tl_tracks:
            position = self._tl_tracks.index(tl_track)
            del self._tl_tracks[position]
        self._increase_version()
        return tl_tracks

    def shuffle(self, start: int | None = None, end: int | None = None) -> None:
        """Shuffles the entire tracklist. If ``start`` and ``end`` is given only
        shuffles the slice ``[start:end]``.

        Triggers the :meth:`mopidy.core.CoreListener.tracklist_changed` event.

        :param start: position of first track to shuffle
        :param end: position after last track to shuffle
        """
        tl_tracks = self._tl_tracks

        # TOOD: use validation helpers?
        if start is not None and end is not None and start >= end:
            raise AssertionError("start must be smaller than end")

        if start is not None and start < 0:
            raise AssertionError("start must be at least zero")

        if end is not None and end > len(tl_tracks):
            raise AssertionError("end can not be larger than tracklist length")

        before = tl_tracks[: start or 0]
        shuffled = tl_tracks[start:end]
        after = tl_tracks[end or len(tl_tracks) :]
        random.shuffle(shuffled)
        self._tl_tracks = before + shuffled + after
        self._increase_version()

    def slice(self, start: int, end: int) -> list[TlTrack]:
        """Returns a slice of the tracklist, limited by the given start and end
        positions.

        :param start: position of first track to include in slice
        :param end: position after last track to include in slice
        """
        # TODO: validate slice?
        return self._tl_tracks[start:end]

    def _mark_playing(self, tl_track: TlTrack) -> None:
        """Internal method for :class:`mopidy.core.PlaybackController`."""
        if self.get_random() and tl_track in self._shuffled:
            self._shuffled.remove(tl_track)

    def _mark_unplayable(self, tl_track: TlTrack | None) -> None:
        """Internal method for :class:`mopidy.core.PlaybackController`."""
        logger.warning(
            "Track is not playable: %s",
            tl_track.track.uri if tl_track else None,
        )
        if self.get_consume() and tl_track is not None:
            self.remove({"tlid": [tl_track.tlid]})
        if self.get_random() and tl_track in self._shuffled:
            self._shuffled.remove(tl_track)

    def _mark_played(self, tl_track: TlTrack | None) -> bool:
        """Internal method for :class:`mopidy.core.PlaybackController`."""
        if self.get_consume() and tl_track is not None:
            self.remove({"tlid": [tl_track.tlid]})
            return True
        return False

    def _trigger_tracklist_changed(self) -> None:
        if self.get_random():
            self._shuffled = self._tl_tracks[:]
            random.shuffle(self._shuffled)
        else:
            self._shuffled = []

        logger.debug("Triggering event: tracklist_changed()")
        listener.CoreListener.send("tracklist_changed")

    def _trigger_options_changed(self) -> None:
        logger.debug("Triggering options changed event")
        listener.CoreListener.send("options_changed")

    def _save_state(self) -> TracklistState:
        return TracklistState(
            tl_tracks=tuple(self._tl_tracks),
            next_tlid=self._next_tlid,
            consume=self.get_consume(),
            random=self.get_random(),
            repeat=self.get_repeat(),
            single=self.get_single(),
        )

    def _load_state(
        self,
        state: TracklistState,
        coverage: Iterable[str],
    ) -> None:
        if state:
            if "mode" in coverage:
                self.set_consume(state.consume)
                self.set_random(state.random)
                self.set_repeat(state.repeat)
                self.set_single(state.single)
            if "tracklist" in coverage:
                self._next_tlid = max(state.next_tlid, self._next_tlid)
                self._tl_tracks = list(state.tl_tracks)
                self._increase_version()


class TracklistControllerProxy:
    get_tl_tracks = proxy_method(TracklistController.get_tl_tracks)
    get_tracks = proxy_method(TracklistController.get_tracks)
    get_length = proxy_method(TracklistController.get_length)
    get_version = proxy_method(TracklistController.get_version)
    get_consume = proxy_method(TracklistController.get_consume)
    set_consume = proxy_method(TracklistController.set_consume)
    get_random = proxy_method(TracklistController.get_random)
    set_random = proxy_method(TracklistController.set_random)
    get_repeat = proxy_method(TracklistController.get_repeat)
    set_repeat = proxy_method(TracklistController.set_repeat)
    get_single = proxy_method(TracklistController.get_single)
    set_single = proxy_method(TracklistController.set_single)
    index = proxy_method(TracklistController.index)
    get_eot_tlid = proxy_method(TracklistController.get_eot_tlid)
    eot_track = proxy_method(TracklistController.eot_track)
    get_next_tlid = proxy_method(TracklistController.get_next_tlid)
    next_track = proxy_method(TracklistController.next_track)
    get_previous_tlid = proxy_method(TracklistController.get_previous_tlid)
    previous_track = proxy_method(TracklistController.previous_track)
    add = proxy_method(TracklistController.add)
    clear = proxy_method(TracklistController.clear)
    filter = proxy_method(TracklistController.filter)
    move = proxy_method(TracklistController.move)
    remove = proxy_method(TracklistController.remove)
    shuffle = proxy_method(TracklistController.shuffle)
    slice = proxy_method(TracklistController.slice)
