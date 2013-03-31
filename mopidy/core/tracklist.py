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

    def get_tl_tracks(self):
        return self._tl_tracks[:]

    tl_tracks = property(get_tl_tracks)
    """
    List of :class:`mopidy.models.TlTrack`.

    Read-only.
    """

    def get_tracks(self):
        return [tl_track.track for tl_track in self._tl_tracks]

    tracks = property(get_tracks)
    """
    List of :class:`mopidy.models.Track` in the tracklist.

    Read-only.
    """

    def get_length(self):
        return len(self._tl_tracks)

    length = property(get_length)
    """Length of the tracklist."""

    def get_version(self):
        return self._version

    def _increase_version(self):
        self._version += 1
        self._core.playback.on_tracklist_change()
        self._trigger_tracklist_changed()

    version = property(get_version)
    """
    The tracklist version.

    Read-only. Integer which is increased every time the tracklist is changed.
    Is not reset before Mopidy is restarted.
    """

    def add(self, tracks=None, at_position=None, uri=None):
        """
        Add the track or list of tracks to the tracklist.

        If ``uri`` is given instead of ``tracks``, the URI is looked up in the
        library and the resulting tracks are added to the tracklist.

        If ``at_position`` is given, the tracks placed at the given position in
        the tracklist. If ``at_position`` is not given, the tracks are appended
        to the end of the tracklist.

        Triggers the :meth:`mopidy.core.CoreListener.tracklist_changed` event.

        :param tracks: tracks to add
        :type tracks: list of :class:`mopidy.models.Track`
        :param at_position: position in tracklist to add track
        :type at_position: int or :class:`None`
        :param uri: URI for tracks to add
        :type uri: string
        :rtype: list of :class:`mopidy.models.TlTrack`
        """
        assert tracks is not None or uri is not None, \
            'tracks or uri must be provided'

        if tracks is None and uri is not None:
            tracks = self._core.library.lookup(uri)

        tl_tracks = []

        for track in tracks:
            tl_track = TlTrack(self._next_tlid, track)
            self._next_tlid += 1
            if at_position is not None:
                self._tl_tracks.insert(at_position, tl_track)
                at_position += 1
            else:
                self._tl_tracks.append(tl_track)
            tl_tracks.append(tl_track)

        if tl_tracks:
            self._increase_version()

        return tl_tracks

    def clear(self):
        """
        Clear the tracklist.

        Triggers the :meth:`mopidy.core.CoreListener.tracklist_changed` event.
        """
        self._tl_tracks = []
        self._increase_version()

    def filter(self, criteria=None, **kwargs):
        """
        Filter the tracklist by the given criterias.

        Examples::

            # Returns track with TLID 7 (tracklist ID)
            filter({'tlid': 7})
            filter(tlid=7)

            # Returns track with ID 1
            filter({'id': 1})
            filter(id=1)

            # Returns track with URI 'xyz'
            filter({'uri': 'xyz'})
            filter(uri='xyz')

            # Returns track with ID 1 and URI 'xyz'
            filter({'id': 1, 'uri': 'xyz'})
            filter(id=1, uri='xyz')

        :param criteria: on or more criteria to match by
        :type criteria: dict
        :rtype: list of :class:`mopidy.models.TlTrack`
        """
        criteria = criteria or kwargs
        matches = self._tl_tracks
        for (key, value) in criteria.iteritems():
            if key == 'tlid':
                matches = filter(lambda ct: ct.tlid == value, matches)
            else:
                matches = filter(
                    lambda ct: getattr(ct.track, key) == value, matches)
        return matches

    def index(self, tl_track):
        """
        Get index of the given :class:`mopidy.models.TlTrack` in the tracklist.

        Raises :exc:`ValueError` if not found.

        :param tl_track: track to find the index of
        :type tl_track: :class:`mopidy.models.TlTrack`
        :rtype: int
        """
        return self._tl_tracks.index(tl_track)

    def move(self, start, end, to_position):
        """
        Move the tracks in the slice ``[start:end]`` to ``to_position``.

        Triggers the :meth:`mopidy.core.CoreListener.tracklist_changed` event.

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
        self._increase_version()

    def remove(self, criteria=None, **kwargs):
        """
        Remove the matching tracks from the tracklist.

        Uses :meth:`filter()` to lookup the tracks to remove.

        Triggers the :meth:`mopidy.core.CoreListener.tracklist_changed` event.

        :param criteria: on or more criteria to match by
        :type criteria: dict
        :rtype: list of :class:`mopidy.models.TlTrack` that was removed
        """
        tl_tracks = self.filter(criteria, **kwargs)
        for tl_track in tl_tracks:
            position = self._tl_tracks.index(tl_track)
            del self._tl_tracks[position]
        self._increase_version()
        return tl_tracks

    def shuffle(self, start=None, end=None):
        """
        Shuffles the entire tracklist. If ``start`` and ``end`` is given only
        shuffles the slice ``[start:end]``.

        Triggers the :meth:`mopidy.core.CoreListener.tracklist_changed` event.

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
        self._increase_version()

    def slice(self, start, end):
        """
        Returns a slice of the tracklist, limited by the given start and end
        positions.

        :param start: position of first track to include in slice
        :type start: int
        :param end: position after last track to include in slice
        :type end: int
        :rtype: :class:`mopidy.models.TlTrack`
        """
        return self._tl_tracks[start:end]

    def _trigger_tracklist_changed(self):
        logger.debug('Triggering event: tracklist_changed()')
        listener.CoreListener.send('tracklist_changed')
