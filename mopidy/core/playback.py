from __future__ import absolute_import, unicode_literals

import logging
import urlparse
import warnings

from mopidy.audio import PlaybackState
from mopidy.core import listener
from mopidy.utils.deprecation import deprecated_property


logger = logging.getLogger(__name__)


class PlaybackController(object):
    pykka_traversable = True

    def __init__(self, backends, core):
        self.backends = backends
        self.core = core

        self._current_tl_track = None
        self._stream_title = None
        self._state = PlaybackState.STOPPED

    def _get_backend(self):
        # TODO: take in track instead
        track = self.get_current_track()
        if track is None:
            return None
        uri = track.uri
        uri_scheme = urlparse.urlparse(uri).scheme
        return self.backends.with_playback.get(uri_scheme, None)

    # Properties

    def get_current_tl_track(self):
        """Get the currently playing or selected track.

        Returns a :class:`mopidy.models.TlTrack` or :class:`None`.
        """
        return self._current_tl_track

    def _set_current_tl_track(self, value):
        """Set the currently playing or selected track.

        *Internal:* This is only for use by Mopidy's test suite.
        """
        self._current_tl_track = value

    current_tl_track = deprecated_property(get_current_tl_track)
    """
    .. deprecated:: 1.0
        Use :meth:`get_current_tl_track` instead.
    """

    def get_current_track(self):
        """
        Get the currently playing or selected track.

        Extracted from :meth:`get_current_tl_track` for convenience.

        Returns a :class:`mopidy.models.Track` or :class:`None`.
        """
        tl_track = self.get_current_tl_track()
        if tl_track is not None:
            return tl_track.track

    current_track = deprecated_property(get_current_track)
    """
    .. deprecated:: 1.0
        Use :meth:`get_current_track` instead.
    """

    def get_stream_title(self):
        """Get the current stream title or :class:`None`."""
        return self._stream_title

    def get_state(self):
        """Get The playback state."""

        return self._state

    def set_state(self, new_state):
        """Set the playback state.

        Must be :attr:`PLAYING`, :attr:`PAUSED`, or :attr:`STOPPED`.

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
        (old_state, self._state) = (self.get_state(), new_state)
        logger.debug('Changing state: %s -> %s', old_state, new_state)

        self._trigger_playback_state_changed(old_state, new_state)

    state = deprecated_property(get_state, set_state)
    """
    .. deprecated:: 1.0
        Use :meth:`get_state` and :meth:`set_state` instead.
    """

    def get_time_position(self):
        """Get time position in milliseconds."""
        backend = self._get_backend()
        if backend:
            return backend.playback.get_time_position().get()
        else:
            return 0

    time_position = deprecated_property(get_time_position)
    """
    .. deprecated:: 1.0
        Use :meth:`get_time_position` instead.
    """

    def get_volume(self):
        """
        .. deprecated:: 1.0
            Use :meth:`core.mixer.get_volume()
            <mopidy.core.MixerController.get_volume>` instead.
        """
        warnings.warn(
            'playback.get_volume() is deprecated', DeprecationWarning)
        return self.core.mixer.get_volume()

    def set_volume(self, volume):
        """
        .. deprecated:: 1.0
            Use :meth:`core.mixer.set_volume()
            <mopidy.core.MixerController.set_volume>` instead.
        """
        warnings.warn(
            'playback.set_volume() is deprecated', DeprecationWarning)
        return self.core.mixer.set_volume(volume)

    volume = deprecated_property(get_volume, set_volume)
    """
    .. deprecated:: 1.0
        Use :meth:`core.mixer.get_volume()
        <mopidy.core.MixerController.get_volume>` and
        :meth:`core.mixer.set_volume()
        <mopidy.core.MixerController.set_volume>` instead.
    """

    def get_mute(self):
        """
        .. deprecated:: 1.0
            Use :meth:`core.mixer.get_mute()
            <mopidy.core.MixerController.get_mute>` instead.
        """
        warnings.warn('playback.get_mute() is deprecated', DeprecationWarning)
        return self.core.mixer.get_mute()

    def set_mute(self, mute):
        """
        .. deprecated:: 1.0
            Use :meth:`core.mixer.set_mute()
            <mopidy.core.MixerController.set_mute>` instead.
        """
        warnings.warn('playback.set_mute() is deprecated', DeprecationWarning)
        return self.core.mixer.set_mute(mute)

    mute = deprecated_property(get_mute, set_mute)
    """
    .. deprecated:: 1.0
        Use :meth:`core.mixer.get_mute()
        <mopidy.core.MixerController.get_mute>` and
        :meth:`core.mixer.set_mute()
        <mopidy.core.MixerController.set_mute>` instead.
    """

    # Methods

    # TODO: remove this.
    def _change_track(self, tl_track, on_error_step=1):
        """
        Change to the given track, keeping the current playback state.

        :param tl_track: track to change to
        :type tl_track: :class:`mopidy.models.TlTrack` or :class:`None`
        :param on_error_step: direction to step at play error, 1 for next
            track (default), -1 for previous track. **INTERNAL**
        :type on_error_step: int, -1 or 1
        """
        old_state = self.get_state()
        self.stop()
        self._set_current_tl_track(tl_track)
        if old_state == PlaybackState.PLAYING:
            self._play(on_error_step=on_error_step)
        elif old_state == PlaybackState.PAUSED:
            self.pause()

    # TODO: this is not really end of track, this is on_need_next_track
    def _on_end_of_track(self):
        """
        Tell the playback controller that end of track is reached.

        Used by event handler in :class:`mopidy.core.Core`.
        """
        if self.get_state() == PlaybackState.STOPPED:
            return

        original_tl_track = self.get_current_tl_track()
        next_tl_track = self.core.tracklist.eot_track(original_tl_track)

        if next_tl_track:
            self._change_track(next_tl_track)
        else:
            self.stop()
            self._set_current_tl_track(None)

        self.core.tracklist._mark_played(original_tl_track)

    def _on_tracklist_change(self):
        """
        Tell the playback controller that the current playlist has changed.

        Used by :class:`mopidy.core.TracklistController`.
        """
        tracklist = self.core.tracklist.get_tl_tracks()
        if self.get_current_tl_track() not in tracklist:
            self.stop()
            self._set_current_tl_track(None)

    def _on_stream_changed(self, uri):
        self._stream_title = None

    def next(self):
        """
        Change to the next track.

        The current playback state will be kept. If it was playing, playing
        will continue. If it was paused, it will still be paused, etc.
        """
        original_tl_track = self.get_current_tl_track()
        next_tl_track = self.core.tracklist.next_track(original_tl_track)

        if next_tl_track:
            # TODO: switch to:
            # backend.play(track)
            # wait for state change?
            self._change_track(next_tl_track)
        else:
            self.stop()
            self._set_current_tl_track(None)

        self.core.tracklist._mark_played(original_tl_track)

    def pause(self):
        """Pause playback."""
        backend = self._get_backend()
        if not backend or backend.playback.pause().get():
            # TODO: switch to:
            # backend.track(pause)
            # wait for state change?
            self.set_state(PlaybackState.PAUSED)
            self._trigger_track_playback_paused()

    def play(self, tl_track=None):
        """
        Play the given track, or if the given track is :class:`None`, play the
        currently active track.

        :param tl_track: track to play
        :type tl_track: :class:`mopidy.models.TlTrack` or :class:`None`
        """
        self._play(tl_track, on_error_step=1)

    def _play(self, tl_track=None, on_error_step=1):
        if tl_track is None:
            if self.get_state() == PlaybackState.PAUSED:
                return self.resume()

            if self.get_current_tl_track() is not None:
                tl_track = self.get_current_tl_track()
            else:
                if on_error_step == 1:
                    tl_track = self.core.tracklist.next_track(tl_track)
                elif on_error_step == -1:
                    tl_track = self.core.tracklist.previous_track(tl_track)

            if tl_track is None:
                return

        assert tl_track in self.core.tracklist.get_tl_tracks()

        # TODO: switch to:
        # backend.play(track)
        # wait for state change?

        if self.get_state() == PlaybackState.PLAYING:
            self.stop()

        self._set_current_tl_track(tl_track)
        self.set_state(PlaybackState.PLAYING)
        backend = self._get_backend()
        success = False

        if backend:
            backend.playback.prepare_change()
            try:
                success = (
                    backend.playback.change_track(tl_track.track).get() and
                    backend.playback.play().get())
            except TypeError:
                logger.error('%s needs to be updated to work with this '
                             'version of Mopidy.', backend)

        if success:
            self.core.tracklist._mark_playing(tl_track)
            self.core.history._add_track(tl_track.track)
            # TODO: replace with stream-changed
            self._trigger_track_playback_started()
        else:
            self.core.tracklist._mark_unplayable(tl_track)
            if on_error_step == 1:
                # TODO: can cause an endless loop for single track repeat.
                self.next()
            elif on_error_step == -1:
                self.previous()

    def previous(self):
        """
        Change to the previous track.

        The current playback state will be kept. If it was playing, playing
        will continue. If it was paused, it will still be paused, etc.
        """
        tl_track = self.get_current_tl_track()
        # TODO: switch to:
        # self.play(....)
        # wait for state change?
        self._change_track(
            self.core.tracklist.previous_track(tl_track), on_error_step=-1)

    def resume(self):
        """If paused, resume playing the current track."""
        if self.get_state() != PlaybackState.PAUSED:
            return
        backend = self._get_backend()
        if backend and backend.playback.resume().get():
            self.set_state(PlaybackState.PLAYING)
            # TODO: trigger via gst messages
            self._trigger_track_playback_resumed()
        # TODO: switch to:
        # backend.resume()
        # wait for state change?

    def seek(self, time_position):
        """
        Seeks to time position given in milliseconds.

        :param time_position: time position in milliseconds
        :type time_position: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        if not self.core.tracklist.tracks:
            return False

        if self.current_track and self.current_track.length is None:
            return False

        if self.get_state() == PlaybackState.STOPPED:
            self.play()

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

    def stop(self):
        """Stop playing."""
        if self.get_state() != PlaybackState.STOPPED:
            backend = self._get_backend()
            time_position_before_stop = self.get_time_position()
            if not backend or backend.playback.stop().get():
                self.set_state(PlaybackState.STOPPED)
                self._trigger_track_playback_ended(time_position_before_stop)

    def _trigger_track_playback_paused(self):
        logger.debug('Triggering track playback paused event')
        if self.current_track is None:
            return
        listener.CoreListener.send(
            'track_playback_paused',
            tl_track=self.get_current_tl_track(),
            time_position=self.get_time_position())

    def _trigger_track_playback_resumed(self):
        logger.debug('Triggering track playback resumed event')
        if self.current_track is None:
            return
        listener.CoreListener.send(
            'track_playback_resumed',
            tl_track=self.get_current_tl_track(),
            time_position=self.get_time_position())

    def _trigger_track_playback_started(self):
        logger.debug('Triggering track playback started event')
        if self.get_current_tl_track() is None:
            return
        listener.CoreListener.send(
            'track_playback_started',
            tl_track=self.get_current_tl_track())

    def _trigger_track_playback_ended(self, time_position_before_stop):
        logger.debug('Triggering track playback ended event')
        if self.get_current_tl_track() is None:
            return
        listener.CoreListener.send(
            'track_playback_ended',
            tl_track=self.get_current_tl_track(),
            time_position=time_position_before_stop)

    def _trigger_playback_state_changed(self, old_state, new_state):
        logger.debug('Triggering playback state change event')
        listener.CoreListener.send(
            'playback_state_changed',
            old_state=old_state, new_state=new_state)

    def _trigger_seeked(self, time_position):
        logger.debug('Triggering seeked event')
        listener.CoreListener.send('seeked', time_position=time_position)
