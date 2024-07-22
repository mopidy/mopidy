from __future__ import annotations

import copy
import logging
import time
from collections.abc import Iterable
from typing import TYPE_CHECKING

from pykka.typing import proxy_method

from mopidy.internal.models import HistoryState, HistoryTrack
from mopidy.models import Ref, Track

if TYPE_CHECKING:
    from typing import TypeAlias

logger = logging.getLogger(__name__)

History: TypeAlias = list[tuple[int, Ref]]


class HistoryController:
    def __init__(self) -> None:
        self._history: History = []

    def _add_track(self, track: Track) -> None:
        """Add track to the playback history.

        Internal method for :class:`mopidy.core.PlaybackController`.

        :param track: track to add
        """
        if not isinstance(track, Track):
            raise TypeError("Only Track objects can be added to the history")

        timestamp = int(time.time() * 1000)

        name_parts = []
        if track.artists:
            artists_names = [artist.name for artist in track.artists if artist.name]
            if artists_names:
                name_parts.append(", ".join(artists_names))
        if track.name is not None:
            name_parts.append(track.name)
        name = " - ".join(name_parts)
        if track.uri is None:
            return
        ref = Ref.track(uri=track.uri, name=name)
        self._history.insert(0, (timestamp, ref))

    def get_length(self) -> int:
        """Get the number of tracks in the history."""
        return len(self._history)

    def get_history(self) -> History:
        """Get the track history.

        Returns a list of two-tuples with timestamp and a reference to the track.
        The timestamps are milliseconds since epoch.
        """
        return copy.copy(self._history)

    def _save_state(self) -> HistoryState:
        # 500 tracks a 3 minutes -> 24 hours history
        count_max = 500
        count = 1
        history_list: list[HistoryTrack] = []
        for timestamp, track in self._history:
            history_list.append(HistoryTrack(timestamp=timestamp, track=track))
            count += 1
            if count_max < count:
                logger.info("Limiting history to %s tracks", count_max)
                break
        return HistoryState(history=tuple(history_list))

    def _load_state(self, state: HistoryState, coverage: Iterable[str]) -> None:
        if state and "history" in coverage:
            self._history = [(h.timestamp, h.track) for h in state.history]


class HistoryControllerProxy:
    get_length = proxy_method(HistoryController.get_length)
    get_history = proxy_method(HistoryController.get_history)
