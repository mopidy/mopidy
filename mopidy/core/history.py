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
        """
        :param track: track to change to
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
        """
        Returns the number of tracks in the history.
        :returns: The number of tracks in the history.
        :rtype :int
        """
        return len(self._history)

    def get_history(self):
        """
        Returns the history.
        :returns: The history as a list of `mopidy.models.Track`
        :rtype: L{`mopidy.models.Track`}
        """
        return copy.copy(self._history)
