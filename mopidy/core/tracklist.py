from __future__ import unicode_literals

import logging
import random

from mopidy.models import TlTrack

from . import listener


logger = logging.getLogger('mopidy.core')


class TracklistController(object):
    pykka_traversable = True

    def __init__(self, core):
        self._core = core
        self._next_tlid = 0
        self._tl_tracks = []
        self._version = 0

    @property
    def tl_tracks(self):
        """
        List of two-tuples of (TLID integer, :class:`mopidy.models.Track`).

        Read-only.
        """
        return self._tl_tracks[:]

    @property
    def tracks(self):
        """
        List of :class:`mopidy.models.Track` in the tracklist.

        Read-only.
        """
        return [tl_track.track for tl_track in self._tl_tracks]

    @property
    def length(self):
        """
        Length of the tracklist.
        """
        return len(self._tl_tracks)

    @property
    def version(self):
        """
        The tracklist version. Integer which is increased every time the
        tracklist is changed. Is not reset before Mopidy is restarted.
        """
        return self._version

    @version.setter  # noqa
    def version(self, version):
        self._version = version
        self._core.playback.on_tracklist_change()
        self._trigger_tracklist_changed()

    def add(self, track, at_position=None, increase_version=True):
        """
        Add the track to the end of, or at the given position in the tracklist.

        Triggers the :method:`mopidy.core.CoreListener.tracklist_changed`
        event.

        :param track: track to add
        :type track: :class:`mopidy.models.Track`
        :param at_position: position in tracklist to add track
        :type at_position: int or :class:`None`
        :param increase_version: if the tracklist version should be increased
        :type increase_version: :class:`True` or :class:`False`
        :rtype: two-tuple of (TLID integer, :class:`mopidy.models.Track`) that
            was added to the tracklist
        """
        assert at_position <= len(self._tl_tracks), \
            'at_position can not be greater than tracklist length'
        tl_track = TlTrack(self._next_tlid, track)
        if at_position is not None:
            self._tl_tracks.insert(at_position, tl_track)
        else:
            self._tl_tracks.append(tl_track)
        if increase_version:
            self.version += 1
        self._next_tlid += 1
        return tl_track

    def append(self, tracks):
        """
        Append the given tracks to the tracklist.

        Triggers the :method:`mopidy.core.CoreListener.tracklist_changed`
        event.

        :param tracks: tracks to append
        :type tracks: list of :class:`mopidy.models.Track`
        :rtype: list of class:`mopidy.models.TlTrack`
        """
        tl_tracks = []
        for track in tracks:
            tl_tracks.append(self.add(track, increase_version=False))

        if tracks:
            self.version += 1

        return tl_tracks

    def clear(self):
        """
        Clear the tracklist.

        Triggers the :method:`mopidy.core.CoreListener.tracklist_changed`
        event.
        """
        self._tl_tracks = []
        self.version += 1

    def get(self, **criteria):
        """
        Get track by given criterias from tracklist.

        Raises :exc:`LookupError` if a unique match is not found.

        Examples::

            get(tlid=7)             # Returns track with TLID 7 (tracklist ID)
            get(id=1)               # Returns track with ID 1
            get(uri='xyz')          # Returns track with URI 'xyz'
            get(id=1, uri='xyz')    # Returns track with ID 1 and URI 'xyz'

        :param criteria: on or more criteria to match by
        :type criteria: dict
        :rtype: two-tuple (TLID integer, :class:`mopidy.models.Track`)
        """
        matches = self._tl_tracks
        for (key, value) in criteria.iteritems():
            if key == 'tlid':
                matches = filter(lambda ct: ct.tlid == value, matches)
            else:
                matches = filter(
                    lambda ct: getattr(ct.track, key) == value, matches)
        if len(matches) == 1:
            return matches[0]
        criteria_string = ', '.join(
            ['%s=%s' % (k, v) for (k, v) in criteria.iteritems()])
        if len(matches) == 0:
            raise LookupError('"%s" match no tracks' % criteria_string)
        else:
            raise LookupError('"%s" match multiple tracks' % criteria_string)

    def index(self, tl_track):
        """
        Get index of the given (TLID integer, :class:`mopidy.models.Track`)
        two-tuple in the tracklist.

        Raises :exc:`ValueError` if not found.

        :param tl_track: track to find the index of
        :type tl_track: two-tuple (TLID integer, :class:`mopidy.models.Track`)
        :rtype: int
        """
        return self._tl_tracks.index(tl_track)

    def move(self, start, end, to_position):
        """
        Move the tracks in the slice ``[start:end]`` to ``to_position``.

        Triggers the :method:`mopidy.core.CoreListener.tracklist_changed`
        event.

        :param start: position of first track to move
        :type start: int
        :param end: position after last track to move
        :type end: int
        :param to_position: new position for the tracks
        :type to_position: int
        """
        if start == end:
            end += 1

        tl_tracks = self._tl_tracks

        assert start < end, 'start must be smaller than end'
        assert start >= 0, 'start must be at least zero'
        assert end <= len(tl_tracks), \
            'end can not be larger than tracklist length'
        assert to_position >= 0, 'to_position must be at least zero'
        assert to_position <= len(tl_tracks), \
            'to_position can not be larger than tracklist length'

        new_tl_tracks = tl_tracks[:start] + tl_tracks[end:]
        for tl_track in tl_tracks[start:end]:
            new_tl_tracks.insert(to_position, tl_track)
            to_position += 1
        self._tl_tracks = new_tl_tracks
        self.version += 1

    def remove(self, **criteria):
        """
        Remove the track from the tracklist.

        Uses :meth:`get()` to lookup the track to remove.

        Triggers the :method:`mopidy.core.CoreListener.tracklist_changed`
        event.

        :param criteria: on or more criteria to match by
        :type criteria: dict
        """
        tl_track = self.get(**criteria)
        position = self._tl_tracks.index(tl_track)
        del self._tl_tracks[position]
        self.version += 1

    def shuffle(self, start=None, end=None):
        """
        Shuffles the entire tracklist. If ``start`` and ``end`` is given only
        shuffles the slice ``[start:end]``.

        Triggers the :method:`mopidy.core.CoreListener.tracklist_changed`
        event.

        :param start: position of first track to shuffle
        :type start: int or :class:`None`
        :param end: position after last track to shuffle
        :type end: int or :class:`None`
        """
        tl_tracks = self._tl_tracks

        if start is not None and end is not None:
            assert start < end, 'start must be smaller than end'

        if start is not None:
            assert start >= 0, 'start must be at least zero'

        if end is not None:
            assert end <= len(tl_tracks), 'end can not be larger than ' + \
                'tracklist length'

        before = tl_tracks[:start or 0]
        shuffled = tl_tracks[start:end]
        after = tl_tracks[end or len(tl_tracks):]
        random.shuffle(shuffled)
        self._tl_tracks = before + shuffled + after
        self.version += 1

    def slice(self, start, end):
        """
        Returns a slice of the tracklist, limited by the given start and end
        positions.

        :param start: position of first track to include in slice
        :type start: int
        :param end: position after last track to include in slice
        :type end: int
        :rtype: two-tuple of (TLID integer, :class:`mopidy.models.Track`)
        """
        return self._tl_tracks[start:end]

    def _trigger_tracklist_changed(self):
        logger.debug('Triggering event: tracklist_changed()')
        listener.CoreListener.send('tracklist_changed')
