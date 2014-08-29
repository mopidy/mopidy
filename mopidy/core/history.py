from __future__ import unicode_literals

import copy
import datetime
import logging

from mopidy.models import Ref, Track


logger = logging.getLogger(__name__)


class History(object):
    track_list = []

    def add(self, track):
        """
        :param track: track to change to
        :type track: :class:`mopidy.models.Track`
        """
        if type(track) is not Track:
            logger.warning('Cannot add non-Track type object to TrackHistory')
            return

        timestamp = int(datetime.datetime.now().strftime("%s")) * 1000
        name_parts = []
        if track.artists:
            name_parts.append(
                ', '.join([artist.name for artist in track.artists])
            )
        if track.name is not None:
            name_parts.append(track.name)
        ref_name = ' - '.join(name_parts)
        track_ref = Ref.track(uri=track.uri, name=ref_name)

        self.track_list.insert(0, (timestamp, track_ref))

    @property
    def size(self):
        """
        Returns the number of tracks in the history.
        :returns: The number of tracks in the history.
        :rtype :int
        """
        return len(self.track_list)

    def get_history(self):
        """
        Returns the history.
        :returns: The history as a list of `mopidy.models.Track`
        :rtype: L{`mopidy.models.Track`}
        """
        return copy.copy(self.track_list)
