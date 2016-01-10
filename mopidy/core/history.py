from __future__ import absolute_import, unicode_literals

import copy
import logging
import time

from mopidy import models
from mopidy.internal.models import HistoryState, HistoryTrack

logger = logging.getLogger(__name__)


class HistoryController(object):
    pykka_traversable = True

    def __init__(self):
        self._history = []

    def _add_track(self, track):
        """Add track to the playback history.

        Internal method for :class:`mopidy.core.PlaybackController`.

        :param track: track to add
        :type track: :class:`mopidy.models.Track`
        """
        if not isinstance(track, models.Track):
            raise TypeError('Only Track objects can be added to the history')

        timestamp = int(time.time() * 1000)

        name_parts = []
        if track.artists:
            name_parts.append(
                ', '.join([artist.name for artist in track.artists]))
        if track.name is not None:
            name_parts.append(track.name)
        name = ' - '.join(name_parts)
        ref = models.Ref.track(uri=track.uri, name=name)

        self._history.insert(0, (timestamp, ref))

    def get_length(self):
        """Get the number of tracks in the history.

        :returns: the history length
        :rtype: int
        """
        return len(self._history)

    def get_history(self):
        """Get the track history.

        The timestamps are milliseconds since epoch.

        :returns: the track history
        :rtype: list of (timestamp, :class:`mopidy.models.Ref`) tuples
        """
        return copy.copy(self._history)

    def _export_state(self):
        """Internal method for :class:`mopidy.Core`."""
        history_list = []
        for timestamp, track in self._history:
            history_list.append(HistoryTrack(
                                timestamp=timestamp, track=track))
        return HistoryState(history=history_list)

    def _restore_state(self, state, coverage):
        """Internal method for :class:`mopidy.Core`."""
        if state:
            if 'history' in coverage:
                self._history = []
                for htrack in state.history:
                    self._history.append((htrack.timestamp, htrack.track))
