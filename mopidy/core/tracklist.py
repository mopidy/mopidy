from __future__ import absolute_import, unicode_literals

import collections
import logging
import random

from mopidy import compat
from mopidy.core import listener
from mopidy.models import TlTrack
from mopidy.utils.deprecation import deprecated_property


logger = logging.getLogger(__name__)


class TracklistController(object):
    pykka_traversable = True

    def __init__(self, core):
        self.core = core
        self._next_tlid = 0
        self._tl_tracks = []
        self._version = 0

        self._shuffled = []

    # Properties

    def get_tl_tracks(self):
        """Get tracklist as list of :class:`mopidy.models.TlTrack`."""
        return self._tl_tracks[:]

    tl_tracks = deprecated_property(get_tl_tracks)
    """
    .. deprecated:: 1.0
        Use :meth:`get_tl_tracks` instead.
    """

    def get_tracks(self):
        """Get tracklist as list of :class:`mopidy.models.Track`."""
        return [tl_track.track for tl_track in self._tl_tracks]

    tracks = deprecated_property(get_tracks)
    """
    .. deprecated:: 1.0
        Use :meth:`get_tracks` instead.
    """

    def get_length(self):
        """Get length of the tracklist."""
        return len(self._tl_tracks)

    length = deprecated_property(get_length)
    """
    .. deprecated:: 1.0
        Use :meth:`get_length` instead.
    """

    def get_version(self):
        """
        Get the tracklist version.

        Integer which is increased every time the tracklist is changed. Is not
        reset before Mopidy is restarted.
        """
        return self._version

    def _increase_version(self):
        self._version += 1
        self.core.playback._on_tracklist_change()
        self._trigger_tracklist_changed()

    version = deprecated_property(get_version)
    """
    .. deprecated:: 1.0
        Use :meth:`get_version` instead.
    """

    def get_consume(self):
        """Get consume mode.

        :class:`True`
            Tracks are removed from the tracklist when they have been played.
        :class:`False`
            Tracks are not removed from the tracklist.
        """
        return getattr(self, '_consume', False)

    def set_consume(self, value):
        """Set consume mode.

        :class:`True`
            Tracks are removed from the tracklist when they have been played.
        :class:`False`
            Tracks are not removed from the tracklist.
        """
        if self.get_consume() != value:
            self._trigger_options_changed()
        return setattr(self, '_consume', value)

    consume = deprecated_property(get_consume, set_consume)
    """
    .. deprecated:: 1.0
        Use :meth:`get_consume` and :meth:`set_consume` instead.
    """

    def get_random(self):
        """Get random mode.

        :class:`True`
            Tracks are selected at random from the tracklist.
        :class:`False`
            Tracks are played in the order of the tracklist.
        """
        return getattr(self, '_random', False)

    def set_random(self, value):
        """Set random mode.

        :class:`True`
            Tracks are selected at random from the tracklist.
        :class:`False`
            Tracks are played in the order of the tracklist.
        """

        if self.get_random() != value:
            self._trigger_options_changed()
        if value:
            self._shuffled = self.get_tl_tracks()
            random.shuffle(self._shuffled)
        return setattr(self, '_random', value)

    random = deprecated_property(get_random, set_random)
    """
    .. deprecated:: 1.0
        Use :meth:`get_random` and :meth:`set_random` instead.
    """

    def get_repeat(self):
        """
        Get repeat mode.

        :class:`True`
            The tracklist is played repeatedly.
        :class:`False`
            The tracklist is played once.
        """
        return getattr(self, '_repeat', False)

    def set_repeat(self, value):
        """
        Set repeat mode.

        To repeat a single track, set both ``repeat`` and ``single``.

        :class:`True`
            The tracklist is played repeatedly.
        :class:`False`
            The tracklist is played once.
        """

        if self.get_repeat() != value:
            self._trigger_options_changed()
        return setattr(self, '_repeat', value)

    repeat = deprecated_property(get_repeat, set_repeat)
    """
    .. deprecated:: 1.0
        Use :meth:`get_repeat` and :meth:`set_repeat` instead.
    """

    def get_single(self):
        """
        Get single mode.

        :class:`True`
            Playback is stopped after current song, unless in ``repeat`` mode.
        :class:`False`
            Playback continues after current song.
        """
        return getattr(self, '_single', False)

    def set_single(self, value):
        """
        Set single mode.

        :class:`True`
            Playback is stopped after current song, unless in ``repeat`` mode.
        :class:`False`
            Playback continues after current song.
        """
        if self.get_single() != value:
            self._trigger_options_changed()
        return setattr(self, '_single', value)

    single = deprecated_property(get_single, set_single)
    """
    .. deprecated:: 1.0
        Use :meth:`get_single` and :meth:`set_single` instead.
    """

    # Methods

    def index(self, tl_track):
        """
        The position of the given track in the tracklist.

        :param tl_track: the track to find the index of
        :type tl_track: :class:`mopidy.models.TlTrack`
        :rtype: :class:`int` or :class:`None`
        """
        try:
            return self._tl_tracks.index(tl_track)
        except ValueError:
            return None

    def eot_track(self, tl_track):
        """
        The track that will be played after the given track.

        Not necessarily the same track as :meth:`next_track`.

        :param tl_track: the reference track
        :type tl_track: :class:`mopidy.models.TlTrack` or :class:`None`
        :rtype: :class:`mopidy.models.TlTrack` or :class:`None`
        """
        if self.get_single() and self.get_repeat():
            return tl_track
        elif self.get_single():
            return None

        # Current difference between next and EOT handling is that EOT needs to
        # handle "single", with that out of the way the rest of the logic is
        # shared.
        return self.next_track(tl_track)

    def next_track(self, tl_track):
        """
        The track that will be played if calling
        :meth:`mopidy.core.PlaybackController.next()`.

        For normal playback this is the next track in the tracklist. If repeat
        is enabled the next track can loop around the tracklist. When random is
        enabled this should be a random track, all tracks should be played once
        before the tracklist repeats.

        :param tl_track: the reference track
        :type tl_track: :class:`mopidy.models.TlTrack` or :class:`None`
        :rtype: :class:`mopidy.models.TlTrack` or :class:`None`
        """

        if not self.get_tl_tracks():
            return None

        if self.get_random() and not self._shuffled:
            if self.get_repeat() or not tl_track:
                logger.debug('Shuffling tracks')
                self._shuffled = self.get_tl_tracks()
                random.shuffle(self._shuffled)

        if self.get_random():
            try:
                return self._shuffled[0]
            except IndexError:
                return None

        if tl_track is None:
            return self.get_tl_tracks()[0]

        next_index = self.index(tl_track) + 1
        if self.get_repeat():
            next_index %= len(self.get_tl_tracks())

        try:
            return self.get_tl_tracks()[next_index]
        except IndexError:
            return None

    def previous_track(self, tl_track):
        """
        Returns the track that will be played if calling
        :meth:`mopidy.core.PlaybackController.previous()`.

        For normal playback this is the previous track in the tracklist. If
        random and/or consume is enabled it should return the current track
        instead.

        :param tl_track: the reference track
        :type tl_track: :class:`mopidy.models.TlTrack` or :class:`None`
        :rtype: :class:`mopidy.models.TlTrack` or :class:`None`
        """
        if self.get_repeat() or self.get_consume() or self.get_random():
            return tl_track

        position = self.index(tl_track)

        if position in (None, 0):
            return None

        return self.get_tl_tracks()[position - 1]

    def add(self, tracks=None, at_position=None, uri=None, uris=None):
        """
        Add the track or list of tracks to the tracklist.

        If ``uri`` is given instead of ``tracks``, the URI is looked up in the
        library and the resulting tracks are added to the tracklist.

        If ``uris`` is given instead of ``tracks``, the URIs are looked up in
        the library and the resulting tracks are added to the tracklist.

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

        .. versionadded:: 1.0
            The ``uris`` argument.

        .. deprecated:: 1.0
            The ``tracks`` and ``uri`` arguments. Use ``uris``.
        """
        assert tracks is not None or uri is not None or uris is not None, \
            'tracks, uri or uris must be provided'

        if tracks is None:
            if uri is not None:
                tracks = self.core.library.lookup(uri=uri)
            elif uris is not None:
                tracks = []
                track_map = self.core.library.lookup(uris=uris)
                for uri in uris:
                    tracks.extend(track_map[uri])

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

        A criteria consists of a model field to check and a list of values to
        compare it against. If the model field matches one of the values, it
        may be returned.

        Only tracks that matches all the given criterias are returned.

        Examples::

            # Returns tracks with TLIDs 1, 2, 3, or 4 (tracklist ID)
            filter({'tlid': [1, 2, 3, 4]})
            filter(tlid=[1, 2, 3, 4])

            # Returns track with IDs 1, 5, or 7
            filter({'id': [1, 5, 7]})
            filter(id=[1, 5, 7])

            # Returns track with URIs 'xyz' or 'abc'
            filter({'uri': ['xyz', 'abc']})
            filter(uri=['xyz', 'abc'])

            # Returns tracks with ID 1 and URI 'xyz'
            filter({'id': [1], 'uri': ['xyz']})
            filter(id=[1], uri=['xyz'])

            # Returns track with a matching ID (1, 3 or 6) and a matching URI
            # ('xyz' or 'abc')
            filter({'id': [1, 3, 6], 'uri': ['xyz', 'abc']})
            filter(id=[1, 3, 6], uri=['xyz', 'abc'])

        :param criteria: on or more criteria to match by
        :type criteria: dict, of (string, list) pairs
        :rtype: list of :class:`mopidy.models.TlTrack`
        """
        criteria = criteria or kwargs
        matches = self._tl_tracks
        for (key, values) in criteria.items():
            if (not isinstance(values, collections.Iterable) or
                    isinstance(values, compat.string_types)):
                # Fail hard if anyone is using the <0.17 calling style
                raise ValueError('Filter values must be iterable: %r' % values)
            if key == 'tlid':
                matches = [ct for ct in matches if ct.tlid in values]
            else:
                matches = [
                    ct for ct in matches if getattr(ct.track, key) in values]
        return matches

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

    def _mark_playing(self, tl_track):
        """Internal method for :class:`mopidy.core.PlaybackController`."""
        if self.get_random() and tl_track in self._shuffled:
            self._shuffled.remove(tl_track)

    def _mark_unplayable(self, tl_track):
        """Internal method for :class:`mopidy.core.PlaybackController`."""
        logger.warning('Track is not playable: %s', tl_track.track.uri)
        if self.get_random() and tl_track in self._shuffled:
            self._shuffled.remove(tl_track)

    def _mark_played(self, tl_track):
        """Internal method for :class:`mopidy.core.PlaybackController`."""
        if self.consume and tl_track is not None:
            self.remove(tlid=[tl_track.tlid])
            return True
        return False

    def _trigger_tracklist_changed(self):
        if self.get_random():
            self._shuffled = self.get_tl_tracks()
            random.shuffle(self._shuffled)
        else:
            self._shuffled = []

        logger.debug('Triggering event: tracklist_changed()')
        listener.CoreListener.send('tracklist_changed')

    def _trigger_options_changed(self):
        logger.debug('Triggering options changed event')
        listener.CoreListener.send('options_changed')
