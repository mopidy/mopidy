from copy import copy
import logging
import random

from mopidy.listeners import BackendListener
from mopidy.models import CpTrack

logger = logging.getLogger('mopidy.backends.base')

class CurrentPlaylistController(object):
    """
    :param backend: backend the controller is a part of
    :type backend: :class:`mopidy.backends.base.Backend`
    """

    pykka_traversable = True

    def __init__(self, backend):
        self.backend = backend
        self.cp_id = 0
        self._cp_tracks = []
        self._version = 0

    @property
    def cp_tracks(self):
        """
        List of two-tuples of (CPID integer, :class:`mopidy.models.Track`).

        Read-only.
        """
        return [copy(cp_track) for cp_track in self._cp_tracks]

    @property
    def tracks(self):
        """
        List of :class:`mopidy.models.Track` in the current playlist.

        Read-only.
        """
        return [cp_track.track for cp_track in self._cp_tracks]

    @property
    def length(self):
        """
        Length of the current playlist.
        """
        return len(self._cp_tracks)

    @property
    def version(self):
        """
        The current playlist version. Integer which is increased every time the
        current playlist is changed. Is not reset before Mopidy is restarted.
        """
        return self._version

    @version.setter
    def version(self, version):
        self._version = version
        self.backend.playback.on_current_playlist_change()
        self._trigger_playlist_changed()

    def add(self, track, at_position=None, increase_version=True):
        """
        Add the track to the end of, or at the given position in the current
        playlist.

        :param track: track to add
        :type track: :class:`mopidy.models.Track`
        :param at_position: position in current playlist to add track
        :type at_position: int or :class:`None`
        :rtype: two-tuple of (CPID integer, :class:`mopidy.models.Track`) that
            was added to the current playlist playlist
        """
        assert at_position <= len(self._cp_tracks), \
            u'at_position can not be greater than playlist length'
        cp_track = CpTrack(self.cp_id, track)
        if at_position is not None:
            self._cp_tracks.insert(at_position, cp_track)
        else:
            self._cp_tracks.append(cp_track)
        if increase_version:
            self.version += 1
        self.cp_id += 1
        return cp_track

    def append(self, tracks):
        """
        Append the given tracks to the current playlist.

        :param tracks: tracks to append
        :type tracks: list of :class:`mopidy.models.Track`
        """
        for track in tracks:
            self.add(track, increase_version=False)

        if tracks:
            self.version += 1

    def clear(self):
        """Clear the current playlist."""
        self._cp_tracks = []
        self.version += 1

    def get(self, **criteria):
        """
        Get track by given criterias from current playlist.

        Raises :exc:`LookupError` if a unique match is not found.

        Examples::

            get(cpid=7)             # Returns track with CPID 7
                                    # (current playlist ID)
            get(id=1)               # Returns track with ID 1
            get(uri='xyz')          # Returns track with URI 'xyz'
            get(id=1, uri='xyz')    # Returns track with ID 1 and URI 'xyz'

        :param criteria: on or more criteria to match by
        :type criteria: dict
        :rtype: two-tuple (CPID integer, :class:`mopidy.models.Track`)
        """
        matches = self._cp_tracks
        for (key, value) in criteria.iteritems():
            if key == 'cpid':
                matches = filter(lambda ct: ct.cpid == value, matches)
            else:
                matches = filter(lambda ct: getattr(ct.track, key) == value,
                    matches)
        if len(matches) == 1:
            return matches[0]
        criteria_string = ', '.join(
            ['%s=%s' % (k, v) for (k, v) in criteria.iteritems()])
        if len(matches) == 0:
            raise LookupError(u'"%s" match no tracks' % criteria_string)
        else:
            raise LookupError(u'"%s" match multiple tracks' % criteria_string)

    def index(self, cp_track):
        """
        Get index of the given (CPID integer, :class:`mopidy.models.Track`)
        two-tuple in the current playlist.

        Raises :exc:`ValueError` if not found.

        :param cp_track: track to find the index of
        :type cp_track: two-tuple (CPID integer, :class:`mopidy.models.Track`)
        :rtype: int
        """
        return self._cp_tracks.index(cp_track)

    def move(self, start, end, to_position):
        """
        Move the tracks in the slice ``[start:end]`` to ``to_position``.

        :param start: position of first track to move
        :type start: int
        :param end: position after last track to move
        :type end: int
        :param to_position: new position for the tracks
        :type to_position: int
        """
        if start == end:
            end += 1

        cp_tracks = self._cp_tracks

        assert start < end, 'start must be smaller than end'
        assert start >= 0, 'start must be at least zero'
        assert end <= len(cp_tracks), \
            'end can not be larger than playlist length'
        assert to_position >= 0, 'to_position must be at least zero'
        assert to_position <= len(cp_tracks), \
            'to_position can not be larger than playlist length'

        new_cp_tracks = cp_tracks[:start] + cp_tracks[end:]
        for cp_track in cp_tracks[start:end]:
            new_cp_tracks.insert(to_position, cp_track)
            to_position += 1
        self._cp_tracks = new_cp_tracks
        self.version += 1

    def remove(self, **criteria):
        """
        Remove the track from the current playlist.

        Uses :meth:`get()` to lookup the track to remove.

        :param criteria: on or more criteria to match by
        :type criteria: dict
        """
        cp_track = self.get(**criteria)
        position = self._cp_tracks.index(cp_track)
        del self._cp_tracks[position]
        self.version += 1

    def shuffle(self, start=None, end=None):
        """
        Shuffles the entire playlist. If ``start`` and ``end`` is given only
        shuffles the slice ``[start:end]``.

        :param start: position of first track to shuffle
        :type start: int or :class:`None`
        :param end: position after last track to shuffle
        :type end: int or :class:`None`
        """
        cp_tracks = self._cp_tracks

        if start is not None and end is not None:
            assert start < end, 'start must be smaller than end'

        if start is not None:
            assert start >= 0, 'start must be at least zero'

        if end is not None:
            assert end <= len(cp_tracks), 'end can not be larger than ' + \
                'playlist length'

        before = cp_tracks[:start or 0]
        shuffled = cp_tracks[start:end]
        after = cp_tracks[end or len(cp_tracks):]
        random.shuffle(shuffled)
        self._cp_tracks = before + shuffled + after
        self.version += 1

    def slice(self, start, end):
        """
        Returns a slice of the current playlist, limited by the given
        start and end positions.

        :param start: position of first track to include in slice
        :type start: int
        :param end: position after last track to include in slice
        :type end: int
        :rtype: two-tuple of (CPID integer, :class:`mopidy.models.Track`)
        """
        return [copy(cp_track) for cp_track in self._cp_tracks[start:end]]

    def _trigger_playlist_changed(self):
        logger.debug(u'Triggering playlist changed event')
        BackendListener.send('playlist_changed')
