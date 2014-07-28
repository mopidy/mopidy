from __future__ import unicode_literals

import logging

from mopidy.models import Track


logger = logging.getLogger(__name__)


class TrackHistory():
    track_list = []

    def add_track(self, track):
        """
        :param track: track to change to
        :type track: :class:`mopidy.models.Track`
        """
        if type(track) is not Track:
            logger.warning('Cannot add non-Track type object to TrackHistory')
            return

        # Reorder the track history if the track is already present.
        if track in self.track_list:
            self.track_list.remove(track)
        self.track_list.insert(0, track)

    def get_history_size(self):
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
        return self.track_list
