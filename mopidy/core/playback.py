from __future__ import unicode_literals

import logging
import random
import urlparse

from mopidy.audio import PlaybackState

from . import listener


logger = logging.getLogger('mopidy.core')


class PlaybackController(object):
    pykka_traversable = True

    def __init__(self, audio, backends, core):
        self.audio = audio
        self.backends = backends
        self.core = core

        self._state = PlaybackState.STOPPED
        self._shuffled = []
        self._first_shuffle = True
        self._volume = None

    def _get_backend(self):
        if self.current_tl_track is None:
            return None
        uri = self.current_tl_track.track.uri
        uri_scheme = urlparse.urlparse(uri).scheme
        return self.backends.with_playback_by_uri_scheme.get(uri_scheme, None)

    ### Properties

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

    def get_current_tl_track(self):
        return self.current_tl_track

    current_tl_track = None
    """
    The currently playing or selected :class:`mopidy.models.TlTrack`, or
    :class:`None`.
    """

    def get_current_track(self):
        return self.current_tl_track and self.current_tl_track.track

    current_track = property(get_current_track)
    """
    The currently playing or selected :class:`mopidy.models.Track`.

    Read-only. Extracted from :attr:`current_tl_track` for convenience.
    """

    def get_random(self):
        return getattr(self, '_random', False)

    def set_random(self, value):
        if self.get_random() != value:
            self._trigger_options_changed()
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

    def get_state(self):
        return self._state

    def set_state(self, new_state):
        (old_state, self._state) = (self.state, new_state)
        logger.debug('Changing state: %s -> %s', old_state, new_state)

        self._trigger_playback_state_changed(old_state, new_state)

    state = property(get_state, set_state)
    """
    The playback state. Must be :attr:`PLAYING`, :attr:`PAUSED`, or
    :attr:`STOPPED`.

    Possible states and transitions:

    .. digraph:: state_transitions

        "STOPPED" -> "PLAYING" [ label="play" ]
        "STOPPED" -> "PAUSED" [ label="pause" ]
        "PLAYING" -> "STOPPED" [ label="stop" ]
        "PLAYING" -> "PAUSED" [ label="pause" ]
        "PLAYING" -> "PLAYING" [ label="play" ]
        "PAUSED" -> "PLAYING" [ label="resume" ]
        "PAUSED" -> "STOPPED" [ label="stop" ]
    """

    def get_time_position(self):
        backend = self._get_backend()
        if backend:
            return backend.playback.get_time_position().get()
        else:
            return 0

    time_position = property(get_time_position)
    """Time position in milliseconds."""

    def get_tracklist_position(self):
        if self.current_tl_track is None:
            return None
        try:
            return self.core.tracklist.tl_tracks.index(self.current_tl_track)
        except ValueError:
            return None

    tracklist_position = property(get_tracklist_position)
    """
    The position of the current track in the tracklist.

    Read-only.
    """

    def get_tl_track_at_eot(self):
        tl_tracks = self.core.tracklist.tl_tracks

        if not tl_tracks:
            return None

        if self.random and not self._shuffled:
            if self.repeat or self._first_shuffle:
                logger.debug('Shuffling tracks')
                self._shuffled = tl_tracks
                random.shuffle(self._shuffled)
                self._first_shuffle = False

        if self.random and self._shuffled:
            return self._shuffled[0]

        if self.current_tl_track is None:
            return tl_tracks[0]

        if self.repeat and self.single:
            return tl_tracks[self.tracklist_position]

        if self.repeat and not self.single:
            return tl_tracks[(self.tracklist_position + 1) % len(tl_tracks)]

        try:
            return tl_tracks[self.tracklist_position + 1]
        except IndexError:
            return None

    tl_track_at_eot = property(get_tl_track_at_eot)
    """
    The track that will be played at the end of the current track.

    Read-only. A :class:`mopidy.models.TlTrack`.

    Not necessarily the same track as :attr:`tl_track_at_next`.
    """

    def get_tl_track_at_next(self):
        tl_tracks = self.core.tracklist.tl_tracks

        if not tl_tracks:
            return None

        if self.random and not self._shuffled:
            if self.repeat or self._first_shuffle:
                logger.debug('Shuffling tracks')
                self._shuffled = tl_tracks
                random.shuffle(self._shuffled)
                self._first_shuffle = False

        if self.random and self._shuffled:
            return self._shuffled[0]

        if self.current_tl_track is None:
            return tl_tracks[0]

        if self.repeat:
            return tl_tracks[(self.tracklist_position + 1) % len(tl_tracks)]

        try:
            return tl_tracks[self.tracklist_position + 1]
        except IndexError:
            return None

    tl_track_at_next = property(get_tl_track_at_next)
    """
    The track that will be played if calling :meth:`next()`.

    Read-only. A :class:`mopidy.models.TlTrack`.

    For normal playback this is the next track in the playlist. If repeat
    is enabled the next track can loop around the playlist. When random is
    enabled this should be a random track, all tracks should be played once
    before the list repeats.
    """

    def get_tl_track_at_previous(self):
        if self.repeat or self.consume or self.random:
            return self.current_tl_track

        if self.tracklist_position in (None, 0):
            return None

        return self.core.tracklist.tl_tracks[self.tracklist_position - 1]

    tl_track_at_previous = property(get_tl_track_at_previous)
    """
    The track that will be played if calling :meth:`previous()`.

    A :class:`mopidy.models.TlTrack`.

    For normal playback this is the previous track in the playlist. If
    random and/or consume is enabled it should return the current track
    instead.
    """

    def get_volume(self):
        if self.audio:
            return self.audio.get_volume().get()
        else:
            # For testing
            return self._volume

    def set_volume(self, volume):
        if self.audio:
            self.audio.set_volume(volume)
        else:
            # For testing
            self._volume = volume

        self._trigger_volume_changed(volume)

    volume = property(get_volume, set_volume)
    """Volume as int in range [0..100] or :class:`None`"""

    ### Methods

    def change_track(self, tl_track, on_error_step=1):
        """
        Change to the given track, keeping the current playback state.

        :param tl_track: track to change to
        :type tl_track: :class:`mopidy.models.TlTrack` or :class:`None`
        :param on_error_step: direction to step at play error, 1 for next
            track (default), -1 for previous track
        :type on_error_step: int, -1 or 1
        """
        old_state = self.state
        self.stop()
        self.current_tl_track = tl_track
        if old_state == PlaybackState.PLAYING:
            self.play(on_error_step=on_error_step)
        elif old_state == PlaybackState.PAUSED:
            self.pause()

    def on_end_of_track(self):
        """
        Tell the playback controller that end of track is reached.

        Used by event handler in :class:`mopidy.core.Core`.
        """
        if self.state == PlaybackState.STOPPED:
            return

        original_tl_track = self.current_tl_track

        if self.tl_track_at_eot:
            self._trigger_track_playback_ended()
            self.play(self.tl_track_at_eot)
        else:
            self.stop(clear_current_track=True)

        if self.consume:
            self.core.tracklist.remove(tlid=original_tl_track.tlid)

    def on_tracklist_change(self):
        """
        Tell the playback controller that the current playlist has changed.

        Used by :class:`mopidy.core.TracklistController`.
        """
        self._first_shuffle = True
        self._shuffled = []

        if (not self.core.tracklist.tl_tracks or
                self.current_tl_track not in
                self.core.tracklist.tl_tracks):
            self.stop(clear_current_track=True)

    def next(self):
        """
        Change to the next track.

        The current playback state will be kept. If it was playing, playing
        will continue. If it was paused, it will still be paused, etc.
        """
        if self.tl_track_at_next:
            self._trigger_track_playback_ended()
            self.change_track(self.tl_track_at_next)
        else:
            self.stop(clear_current_track=True)

    def pause(self):
        """Pause playback."""
        backend = self._get_backend()
        if not backend or backend.playback.pause().get():
            self.state = PlaybackState.PAUSED
            self._trigger_track_playback_paused()

    def play(self, tl_track=None, on_error_step=1):
        """
        Play the given track, or if the given track is :class:`None`, play the
        currently active track.

        :param tl_track: track to play
        :type tl_track: :class:`mopidy.models.TlTrack` or :class:`None`
        :param on_error_step: direction to step at play error, 1 for next
            track (default), -1 for previous track
        :type on_error_step: int, -1 or 1
        """

        if tl_track is not None:
            assert tl_track in self.core.tracklist.tl_tracks
        elif tl_track is None:
            if self.state == PlaybackState.PAUSED:
                return self.resume()
            elif self.current_tl_track is not None:
                tl_track = self.current_tl_track
            elif self.current_tl_track is None and on_error_step == 1:
                tl_track = self.tl_track_at_next
            elif self.current_tl_track is None and on_error_step == -1:
                tl_track = self.tl_track_at_previous

        if tl_track is not None:
            self.current_tl_track = tl_track
            self.state = PlaybackState.PLAYING
            backend = self._get_backend()
            if not backend or not backend.playback.play(tl_track.track).get():
                logger.warning('Track is not playable: %s', tl_track.track.uri)
                if self.random and self._shuffled:
                    self._shuffled.remove(tl_track)
                if on_error_step == 1:
                    # TODO: can cause an endless loop for single track repeat.
                    self.next()
                elif on_error_step == -1:
                    self.previous()
                return

        if self.random and self.current_tl_track in self._shuffled:
            self._shuffled.remove(self.current_tl_track)

        self._trigger_track_playback_started()

    def previous(self):
        """
        Change to the previous track.

        The current playback state will be kept. If it was playing, playing
        will continue. If it was paused, it will still be paused, etc.
        """
        self._trigger_track_playback_ended()
        self.change_track(self.tl_track_at_previous, on_error_step=-1)

    def resume(self):
        """If paused, resume playing the current track."""
        if self.state != PlaybackState.PAUSED:
            return
        backend = self._get_backend()
        if backend and backend.playback.resume().get():
            self.state = PlaybackState.PLAYING
            self._trigger_track_playback_resumed()

    def seek(self, time_position):
        """
        Seeks to time position given in milliseconds.

        :param time_position: time position in milliseconds
        :type time_position: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        if not self.core.tracklist.tracks:
            return False

        if self.state == PlaybackState.STOPPED:
            self.play()
        elif self.state == PlaybackState.PAUSED:
            self.resume()

        if time_position < 0:
            time_position = 0
        elif time_position > self.current_track.length:
            self.next()
            return True

        backend = self._get_backend()
        if not backend:
            return False

        success = backend.playback.seek(time_position).get()
        if success:
            self._trigger_seeked(time_position)
        return success

    def stop(self, clear_current_track=False):
        """
        Stop playing.

        :param clear_current_track: whether to clear the current track _after_
            stopping
        :type clear_current_track: boolean
        """
        if self.state != PlaybackState.STOPPED:
            backend = self._get_backend()
            if not backend or backend.playback.stop().get():
                self._trigger_track_playback_ended()
                self.state = PlaybackState.STOPPED
        if clear_current_track:
            self.current_tl_track = None

    def _trigger_track_playback_paused(self):
        logger.debug('Triggering track playback paused event')
        if self.current_track is None:
            return
        listener.CoreListener.send(
            'track_playback_paused',
            tl_track=self.current_tl_track, time_position=self.time_position)

    def _trigger_track_playback_resumed(self):
        logger.debug('Triggering track playback resumed event')
        if self.current_track is None:
            return
        listener.CoreListener.send(
            'track_playback_resumed',
            tl_track=self.current_tl_track, time_position=self.time_position)

    def _trigger_track_playback_started(self):
        logger.debug('Triggering track playback started event')
        if self.current_tl_track is None:
            return
        listener.CoreListener.send(
            'track_playback_started',
            tl_track=self.current_tl_track)

    def _trigger_track_playback_ended(self):
        logger.debug('Triggering track playback ended event')
        if self.current_tl_track is None:
            return
        listener.CoreListener.send(
            'track_playback_ended',
            tl_track=self.current_tl_track, time_position=self.time_position)

    def _trigger_playback_state_changed(self, old_state, new_state):
        logger.debug('Triggering playback state change event')
        listener.CoreListener.send(
            'playback_state_changed',
            old_state=old_state, new_state=new_state)

    def _trigger_options_changed(self):
        logger.debug('Triggering options changed event')
        listener.CoreListener.send('options_changed')

    def _trigger_volume_changed(self, volume):
        logger.debug('Triggering volume changed event')
        listener.CoreListener.send('volume_changed', volume=volume)

    def _trigger_seeked(self, time_position):
        logger.debug('Triggering seeked event')
        listener.CoreListener.send('seeked', time_position=time_position)
