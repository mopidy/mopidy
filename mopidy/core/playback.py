import logging
import random

from . import listener


logger = logging.getLogger('mopidy.backends.base')


def option_wrapper(name, default):
    def get_option(self):
        return getattr(self, name, default)

    def set_option(self, value):
        if getattr(self, name, default) != value:
            self._trigger_options_changed()
        return setattr(self, name, value)

    return property(get_option, set_option)


class PlaybackState(object):
    """
    Enum of playback states.
    """

    #: Constant representing the paused state.
    PAUSED = u'paused'

    #: Constant representing the playing state.
    PLAYING = u'playing'

    #: Constant representing the stopped state.
    STOPPED = u'stopped'


class PlaybackController(object):
    """
    :param backend: the backend
    :type backend: :class:`mopidy.backends.base.Backend`
    :param provider: provider the controller should use
    :type provider: instance of :class:`BasePlaybackProvider`
    """

    # pylint: disable = R0902
    # Too many instance attributes

    pykka_traversable = True

    #: :class:`True`
    #:     Tracks are removed from the playlist when they have been played.
    #: :class:`False`
    #:     Tracks are not removed from the playlist.
    consume = option_wrapper('_consume', False)

    #: The currently playing or selected track.
    #:
    #: A two-tuple of (CPID integer, :class:`mopidy.models.Track`) or
    #: :class:`None`.
    current_cp_track = None

    #: :class:`True`
    #:     Tracks are selected at random from the playlist.
    #: :class:`False`
    #:     Tracks are played in the order of the playlist.
    random = option_wrapper('_random', False)

    #: :class:`True`
    #:     The current playlist is played repeatedly. To repeat a single track,
    #:     select both :attr:`repeat` and :attr:`single`.
    #: :class:`False`
    #:     The current playlist is played once.
    repeat = option_wrapper('_repeat', False)

    #: :class:`True`
    #:     Playback is stopped after current song, unless in :attr:`repeat`
    #:     mode.
    #: :class:`False`
    #:     Playback continues after current song.
    single = option_wrapper('_single', False)

    def __init__(self, audio, backend, core):
        self.audio = audio
        self.backend = backend
        self.core = core
        self._state = PlaybackState.STOPPED
        self._shuffled = []
        self._first_shuffle = True
        self._volume = None

    def _get_cpid(self, cp_track):
        if cp_track is None:
            return None
        return cp_track.cpid

    def _get_track(self, cp_track):
        if cp_track is None:
            return None
        return cp_track.track

    @property
    def current_cpid(self):
        """
        The CPID (current playlist ID) of the currently playing or selected
        track.

        Read-only. Extracted from :attr:`current_cp_track` for convenience.
        """
        return self._get_cpid(self.current_cp_track)

    @property
    def current_track(self):
        """
        The currently playing or selected :class:`mopidy.models.Track`.

        Read-only. Extracted from :attr:`current_cp_track` for convenience.
        """
        return self._get_track(self.current_cp_track)

    @property
    def current_playlist_position(self):
        """
        The position of the current track in the current playlist.

        Read-only.
        """
        if self.current_cp_track is None:
            return None
        try:
            return self.core.current_playlist.cp_tracks.index(
                self.current_cp_track)
        except ValueError:
            return None

    @property
    def track_at_eot(self):
        """
        The track that will be played at the end of the current track.

        Read-only. A :class:`mopidy.models.Track` extracted from
        :attr:`cp_track_at_eot` for convenience.
        """
        return self._get_track(self.cp_track_at_eot)

    @property
    def cp_track_at_eot(self):
        """
        The track that will be played at the end of the current track.

        Read-only. A two-tuple of (CPID integer, :class:`mopidy.models.Track`).

        Not necessarily the same track as :attr:`cp_track_at_next`.
        """
        # pylint: disable = R0911
        # Too many return statements

        cp_tracks = self.core.current_playlist.cp_tracks

        if not cp_tracks:
            return None

        if self.random and not self._shuffled:
            if self.repeat or self._first_shuffle:
                logger.debug('Shuffling tracks')
                self._shuffled = cp_tracks
                random.shuffle(self._shuffled)
                self._first_shuffle = False

        if self.random and self._shuffled:
            return self._shuffled[0]

        if self.current_cp_track is None:
            return cp_tracks[0]

        if self.repeat and self.single:
            return cp_tracks[self.current_playlist_position]

        if self.repeat and not self.single:
            return cp_tracks[
                (self.current_playlist_position + 1) % len(cp_tracks)]

        try:
            return cp_tracks[self.current_playlist_position + 1]
        except IndexError:
            return None

    @property
    def track_at_next(self):
        """
        The track that will be played if calling :meth:`next()`.

        Read-only. A :class:`mopidy.models.Track` extracted from
        :attr:`cp_track_at_next` for convenience.
        """
        return self._get_track(self.cp_track_at_next)

    @property
    def cp_track_at_next(self):
        """
        The track that will be played if calling :meth:`next()`.

        Read-only. A two-tuple of (CPID integer, :class:`mopidy.models.Track`).

        For normal playback this is the next track in the playlist. If repeat
        is enabled the next track can loop around the playlist. When random is
        enabled this should be a random track, all tracks should be played once
        before the list repeats.
        """
        cp_tracks = self.core.current_playlist.cp_tracks

        if not cp_tracks:
            return None

        if self.random and not self._shuffled:
            if self.repeat or self._first_shuffle:
                logger.debug('Shuffling tracks')
                self._shuffled = cp_tracks
                random.shuffle(self._shuffled)
                self._first_shuffle = False

        if self.random and self._shuffled:
            return self._shuffled[0]

        if self.current_cp_track is None:
            return cp_tracks[0]

        if self.repeat:
            return cp_tracks[
                (self.current_playlist_position + 1) % len(cp_tracks)]

        try:
            return cp_tracks[self.current_playlist_position + 1]
        except IndexError:
            return None

    @property
    def track_at_previous(self):
        """
        The track that will be played if calling :meth:`previous()`.

        Read-only. A :class:`mopidy.models.Track` extracted from
        :attr:`cp_track_at_previous` for convenience.
        """
        return self._get_track(self.cp_track_at_previous)

    @property
    def cp_track_at_previous(self):
        """
        The track that will be played if calling :meth:`previous()`.

        A two-tuple of (CPID integer, :class:`mopidy.models.Track`).

        For normal playback this is the previous track in the playlist. If
        random and/or consume is enabled it should return the current track
        instead.
        """
        if self.repeat or self.consume or self.random:
            return self.current_cp_track

        if self.current_playlist_position in (None, 0):
            return None

        return self.core.current_playlist.cp_tracks[
            self.current_playlist_position - 1]

    @property
    def state(self):
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
        return self._state

    @state.setter
    def state(self, new_state):
        (old_state, self._state) = (self.state, new_state)
        logger.debug(u'Changing state: %s -> %s', old_state, new_state)

        self._trigger_playback_state_changed(old_state, new_state)

    @property
    def time_position(self):
        """Time position in milliseconds."""
        return self.backend.playback.get_time_position().get()

    @property
    def volume(self):
        """Volume as int in range [0..100] or :class:`None`"""
        if self.audio:
            return self.audio.get_volume().get()
        else:
            # For testing
            return self._volume

    @volume.setter
    def volume(self, volume):
        if self.audio:
            self.audio.set_volume(volume)
        else:
            # For testing
            self._volume = volume

    def change_track(self, cp_track, on_error_step=1):
        """
        Change to the given track, keeping the current playback state.

        :param cp_track: track to change to
        :type cp_track: two-tuple (CPID integer, :class:`mopidy.models.Track`)
            or :class:`None`
        :param on_error_step: direction to step at play error, 1 for next
            track (default), -1 for previous track
        :type on_error_step: int, -1 or 1

        """
        old_state = self.state
        self.stop()
        self.current_cp_track = cp_track
        if old_state == PlaybackState.PLAYING:
            self.play(on_error_step=on_error_step)
        elif old_state == PlaybackState.PAUSED:
            self.pause()

    def on_end_of_track(self):
        """
        Tell the playback controller that end of track is reached.
        """
        if self.state == PlaybackState.STOPPED:
            return

        original_cp_track = self.current_cp_track

        if self.cp_track_at_eot:
            self._trigger_track_playback_ended()
            self.play(self.cp_track_at_eot)
        else:
            self.stop(clear_current_track=True)

        if self.consume:
            self.core.current_playlist.remove(cpid=original_cp_track.cpid)

    def on_current_playlist_change(self):
        """
        Tell the playback controller that the current playlist has changed.

        Used by :class:`mopidy.core.CurrentPlaylistController`.
        """
        self._first_shuffle = True
        self._shuffled = []

        if (not self.core.current_playlist.cp_tracks or
                self.current_cp_track not in
                self.core.current_playlist.cp_tracks):
            self.stop(clear_current_track=True)

    def next(self):
        """
        Change to the next track.

        The current playback state will be kept. If it was playing, playing
        will continue. If it was paused, it will still be paused, etc.
        """
        if self.cp_track_at_next:
            self._trigger_track_playback_ended()
            self.change_track(self.cp_track_at_next)
        else:
            self.stop(clear_current_track=True)

    def pause(self):
        """Pause playback."""
        if self.backend.playback.pause().get():
            self.state = PlaybackState.PAUSED
            self._trigger_track_playback_paused()

    def play(self, cp_track=None, on_error_step=1):
        """
        Play the given track, or if the given track is :class:`None`, play the
        currently active track.

        :param cp_track: track to play
        :type cp_track: two-tuple (CPID integer, :class:`mopidy.models.Track`)
            or :class:`None`
        :param on_error_step: direction to step at play error, 1 for next
            track (default), -1 for previous track
        :type on_error_step: int, -1 or 1
        """

        if cp_track is not None:
            assert cp_track in self.core.current_playlist.cp_tracks
        elif cp_track is None:
            if self.state == PlaybackState.PAUSED:
                return self.resume()
            elif self.current_cp_track is not None:
                cp_track = self.current_cp_track
            elif self.current_cp_track is None and on_error_step == 1:
                cp_track = self.cp_track_at_next
            elif self.current_cp_track is None and on_error_step == -1:
                cp_track = self.cp_track_at_previous

        if cp_track is not None:
            self.current_cp_track = cp_track
            self.state = PlaybackState.PLAYING
            if not self.backend.playback.play(cp_track.track).get():
                # Track is not playable
                if self.random and self._shuffled:
                    self._shuffled.remove(cp_track)
                if on_error_step == 1:
                    self.next()
                elif on_error_step == -1:
                    self.previous()

        if self.random and self.current_cp_track in self._shuffled:
            self._shuffled.remove(self.current_cp_track)

        self._trigger_track_playback_started()

    def previous(self):
        """
        Change to the previous track.

        The current playback state will be kept. If it was playing, playing
        will continue. If it was paused, it will still be paused, etc.
        """
        self._trigger_track_playback_ended()
        self.change_track(self.cp_track_at_previous, on_error_step=-1)

    def resume(self):
        """If paused, resume playing the current track."""
        if (self.state == PlaybackState.PAUSED and
                self.backend.playback.resume().get()):
            self.state = PlaybackState.PLAYING
            self._trigger_track_playback_resumed()

    def seek(self, time_position):
        """
        Seeks to time position given in milliseconds.

        :param time_position: time position in milliseconds
        :type time_position: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        if not self.core.current_playlist.tracks:
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

        success = self.backend.playback.seek(time_position).get()
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
            if self.backend.playback.stop().get():
                self._trigger_track_playback_ended()
                self.state = PlaybackState.STOPPED
        if clear_current_track:
            self.current_cp_track = None

    def _trigger_track_playback_paused(self):
        logger.debug(u'Triggering track playback paused event')
        if self.current_track is None:
            return
        listener.CoreListener.send('track_playback_paused',
            track=self.current_track,
            time_position=self.time_position)

    def _trigger_track_playback_resumed(self):
        logger.debug(u'Triggering track playback resumed event')
        if self.current_track is None:
            return
        listener.CoreListener.send('track_playback_resumed',
            track=self.current_track,
            time_position=self.time_position)

    def _trigger_track_playback_started(self):
        logger.debug(u'Triggering track playback started event')
        if self.current_track is None:
            return
        listener.CoreListener.send('track_playback_started',
            track=self.current_track)

    def _trigger_track_playback_ended(self):
        logger.debug(u'Triggering track playback ended event')
        if self.current_track is None:
            return
        listener.CoreListener.send('track_playback_ended',
            track=self.current_track,
            time_position=self.time_position)

    def _trigger_playback_state_changed(self, old_state, new_state):
        logger.debug(u'Triggering playback state change event')
        listener.CoreListener.send('playback_state_changed',
            old_state=old_state, new_state=new_state)

    def _trigger_options_changed(self):
        logger.debug(u'Triggering options changed event')
        listener.CoreListener.send('options_changed')

    def _trigger_seeked(self, time_position):
        logger.debug(u'Triggering seeked event')
        listener.CoreListener.send('seeked', time_position=time_position)
