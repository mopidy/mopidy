from __future__ import unicode_literals

import logging
import random
import urlparse

from mopidy.models import TlTrack

from . import listener


logger = logging.getLogger('mopidy.core')


class TracklistController(object):
    pykka_traversable = True

    def __init__(self, backends, core):
        self.backends = backends
        self.core = core
        self._next_tlid = 0
        self._tl_tracks = []
        self._version = 0

        self._shuffled = []

    def _get_backend(self, tl_track):
        if tl_track is None:
            return None
        if tl_track.track is None:
            return None
        if tl_track.track.uri is None:
            return None
        uri_scheme = urlparse.urlparse(tl_track.track.uri).scheme
        return self.backends.with_tracklist_by_uri_scheme.get(uri_scheme, None)

    ### Properties

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
        self.core.playback.on_tracklist_change()
        self._trigger_tracklist_changed()

    version = property(get_version)
    """
    The tracklist version.

    Read-only. Integer which is increased every time the tracklist is changed.
    Is not reset before Mopidy is restarted.
    """

    def get_consume(self):
        return getattr(self, '_consume', False)

    def set_consume(self, value):
        if self.get_consume() != value:
            self._trigger_options_changed()
        return setattr(self, '_consume', value)

    consume = property(get_consume, set_consume)
    """
    :class:`True`
        Tracks are removed from the playlist when they have been played.
    :class:`False`
        Tracks are not removed from the playlist.
    """

    def get_random(self):
        return getattr(self, '_random', False)

    def set_random(self, value):
        if self.get_random() != value:
            self._trigger_options_changed()
        if value:
            self._shuffled = self.tl_tracks
            random.shuffle(self._shuffled)
        return setattr(self, '_random', value)

    random = property(get_random, set_random)
    """
    :class:`True`
        Tracks are selected at random from the playlist.
    :class:`False`
        Tracks are played in the order of the playlist.
    """

    def get_repeat(self):
        return getattr(self, '_repeat', False)

    def set_repeat(self, value):
        if self.get_repeat() != value:
            self._trigger_options_changed()
        return setattr(self, '_repeat', value)

    repeat = property(get_repeat, set_repeat)
    """
    :class:`True`
        The current playlist is played repeatedly. To repeat a single track,
        select both :attr:`repeat` and :attr:`single`.
    :class:`False`
        The current playlist is played once.
    """

    def get_single(self):
        return getattr(self, '_single', False)

    def set_single(self, value):
        if self.get_single() != value:
            self._trigger_options_changed()
        return setattr(self, '_single', value)

    single = property(get_single, set_single)
    """
    :class:`True`
        Playback is stopped after current song, unless in :attr:`repeat`
        mode.
    :class:`False`
        Playback continues after current song.
    """

    ### Methods

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
        backend = self._get_backend(tl_track)
        if backend and backend.has_tracklist().get():
            eot_tl_track = backend.tracklist.eot_track(self, tl_track).get()
            if type(eot_tl_track) in [TlTrack, type(None)]:
                return eot_tl_track

        if self.single and self.repeat:
            return tl_track
        elif self.single:
            return None

        # Current difference between next and EOT handling is that EOT needs to
        # handle "single", with that out of the way the rest of the logic is
        # shared.
        return self._next_track(tl_track)

    def next_track(self, tl_track):
        """
        The track that will be played if calling
        :meth:`mopidy.core.PlaybackController.next()`.

        For normal playback this is the next track in the playlist. If repeat
        is enabled the next track can loop around the playlist. When random is
        enabled this should be a random track, all tracks should be played once
        before the list repeats.

        :param tl_track: the reference track
        :type tl_track: :class:`mopidy.models.TlTrack` or :class:`None`
        :rtype: :class:`mopidy.models.TlTrack` or :class:`None`
        """
        backend = self._get_backend(tl_track)
        if backend and backend.has_tracklist().get():
            next_tl_track = backend.tracklist.next_track(self, tl_track).get()
            if type(next_tl_track) in [TlTrack, type(None)]:
                return next_tl_track

        return self._next_track(tl_track)

    def _next_track(self, tl_track):
        if not self.tl_tracks:
            return None

        if self.random and not self._shuffled:
            if self.repeat or not tl_track:
                logger.debug('Shuffling tracks')
                self._shuffled = self.tl_tracks
                random.shuffle(self._shuffled)

        if self.random:
            try:
                return self._shuffled[0]
            except IndexError:
                return None

        if tl_track is None:
            return self.tl_tracks[0]

        next_index = self.index(tl_track) + 1
        if self.repeat:
            next_index %= len(self.tl_tracks)

        try:
            return self.tl_tracks[next_index]
        except IndexError:
            return None

    def previous_track(self, tl_track):
        """
        Returns the track that will be played if calling
        :meth:`mopidy.core.PlaybackController.previous()`.

        For normal playback this is the previous track in the playlist. If
        random and/or consume is enabled it should return the current track
        instead.

        :param tl_track: the reference track
        :type tl_track: :class:`mopidy.models.TlTrack` or :class:`None`
        :rtype: :class:`mopidy.models.TlTrack` or :class:`None`
        """
        backend = self._get_backend(tl_track)
        if backend and backend.has_tracklist().get():
            previous_tl_track = backend.tracklist.previous_track(
                self, tl_track).get()
            if type(previous_tl_track) in [TlTrack, type(None)]:
                return previous_tl_track

        if self.repeat or self.consume or self.random:
            return tl_track

        position = self.index(tl_track)

        if position in (None, 0):
            return None

        return self.tl_tracks[position - 1]

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

        backend = self._get_backend(self.core.playback.current_tl_track)
        if backend and backend.has_tracklist().get():
            tracklist = backend.tracklist.add(self, tracks, at_position,
                                              uri).get()
            if type(tracklist) in [list, ]:
                return tracklist

        if tracks is None and uri is not None:
            tracks = self.core.library.lookup(uri)

        return self._add(tracks, at_position)

    def _add(self, tracks, at_position):
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

        backend = self._get_backend(self.core.playback.current_tl_track)
        if backend and backend.has_tracklist().get():
            if backend.tracklist.move(self, start, end, to_position).get():
                return

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

        backend = self._get_backend(self.core.playback.current_tl_track)
        if backend and backend.has_tracklist().get():
            removed = backend.tracklist.remove(self, tl_tracks).get()
            if type(removed) in [list, ]:
                return removed
        return self._remove(tl_tracks)

    def _remove(self, tl_tracks):
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
        backend = self._get_backend(self.core.playback.current_tl_track)
        if backend and backend.has_tracklist().get():
            if backend.tracklist.shuffle(self, start, end).get():
                return

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

    def mark_playing(self, tl_track):
        """Private method used by :class:`mopidy.core.PlaybackController`."""
        backend = self._get_backend(tl_track)
        if backend and backend.has_tracklist().get():
            result = backend.tracklist.mark_starting(self, tl_track).get()
            if result:
                return result
        if self.random and tl_track in self._shuffled:
            self._shuffled.remove(tl_track)

    def mark_unplayable(self, tl_track):
        """Private method used by :class:`mopidy.core.PlaybackController`."""
        logger.warning('Track is not playable: %s', tl_track.track.uri)
        backend = self._get_backend(tl_track)
        if backend and backend.has_tracklist().get():
            result = backend.tracklist.mark_unplayable(self, tl_track).get()
            if result:
                return result
        if self.random and tl_track in self._shuffled:
            self._shuffled.remove(tl_track)

    def mark_played(self, tl_track):
        """Private method used by :class:`mopidy.core.PlaybackController`."""
        backend = self._get_backend(tl_track)
        if backend and backend.has_tracklist().get():
            result = backend.tracklist.mark_consumed(self, tl_track).get()
            if result in [True, False]:
                return result
        if not self.consume:
            return False
        self.remove(tlid=tl_track.tlid)
        return True

    def mark_metadata(self, tl_track, metadata):
        backend = self._get_backend(tl_track)
        if backend and backend.has_tracklist().get():
            backend.tracklist.mark_metadata(self, tl_track, metadata).get()

    def _trigger_tracklist_changed(self):
        if self.random:
            self._shuffled = self.tl_tracks
            random.shuffle(self._shuffled)
        else:
            self._shuffled = []

        logger.debug('Triggering event: tracklist_changed()')
        listener.CoreListener.send('tracklist_changed')

    def _trigger_options_changed(self):
        logger.debug('Triggering options changed event')
        listener.CoreListener.send('options_changed')
