from __future__ import unicode_literals

import copy
import logging
import time

from mopidy import models


logger = logging.getLogger(__name__)


class HistoryController(object):

    def __init__(self):
        self._history = []

    def add(self, track):
        """Add track to the playback history.

        :param track: track to add
        :type track: :class:`mopidy.models.Track`
        """
        if not isinstance(track, models.Track):
            raise TypeError('Only Track objects can be added to the history')

        timestamp = int(time.time() * 1000)

        name_parts = []
        if track.artists:
            name_parts.append(
                ', '.join([artist.name for artist in track.artists])
            )
        if track.name is not None:
            name_parts.append(track.name)
        ref_name = ' - '.join(name_parts)
        track_ref = models.Ref.track(uri=track.uri, name=ref_name)

        self._history.insert(0, (timestamp, track_ref))

    @property
    def size(self):
        """Get the number of tracks in the history.

        :returns: the history length
        :rtype: int
        """
        return len(self._history)

    def get_history(self):
        """Get the track history.

        :returns: the track history
        :rtype: list of (timestamp, mopidy.models.Ref) tuples
        """
        return copy.copy(self._history)
