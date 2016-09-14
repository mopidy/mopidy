from __future__ import absolute_import, unicode_literals

import logging

from mopidy.audio import PlaybackState
from mopidy.compat import urllib
from mopidy.core import listener
from mopidy.internal import deprecation, models, validation

logger = logging.getLogger(__name__)


class PlaybackController(object):
    pykka_traversable = True

    def __init__(self, audio, backends, core):
        # TODO: these should be internal
        self.backends = backends
        self.core = core
        self._audio = audio

        self._stream_title = None
        self._state = PlaybackState.STOPPED

        self._current_tl_track = None
        self._pending_tl_track = None

        self._pending_position = None
        self._last_position = None
        self._previous = False

        self._start_at_position = None
        self._start_paused = False

        if self._audio:
            self._audio.set_about_to_finish_callback(
                self._on_about_to_finish_callback)

    def _get_backend(self, tl_track):
        if tl_track is None:
            return None
        uri_scheme = urllib.parse.urlparse(tl_track.track.uri).scheme
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

    current_tl_track = deprecation.deprecated_property(get_current_tl_track)
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
        return getattr(self.get_current_tl_track(), 'track', None)

    current_track = deprecation.deprecated_property(get_current_track)
    """
    .. deprecated:: 1.0
        Use :meth:`get_current_track` instead.
    """

    def get_current_tlid(self):
        """
        Get the currently playing or selected TLID.

        Extracted from :meth:`get_current_tl_track` for convenience.

        Returns a :class:`int` or :class:`None`.

        .. versionadded:: 1.1
        """
        return getattr(self.get_current_tl_track(), 'tlid', None)

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
        validation.check_choice(new_state, validation.PLAYBACK_STATES)

        (old_state, self._state) = (self.get_state(), new_state)
        logger.debug('Changing state: %s -> %s', old_state, new_state)

        self._trigger_playback_state_changed(old_state, new_state)

    state = deprecation.deprecated_property(get_state, set_state)
    """
    .. deprecated:: 1.0
        Use :meth:`get_state` and :meth:`set_state` instead.
    """

    def get_time_position(self):
        """Get time position in milliseconds."""
        if self._pending_position is not None:
            return self._pending_position
        backend = self._get_backend(self.get_current_tl_track())
        if backend:
            # TODO: Wrap backend call in error handling.
            return backend.playback.get_time_position().get()
        else:
            return 0

    time_position = deprecation.deprecated_property(get_time_position)
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
        deprecation.warn('core.playback.get_volume')
        return self.core.mixer.get_volume()

    def set_volume(self, volume):
        """
        .. deprecated:: 1.0
            Use :meth:`core.mixer.set_volume()
            <mopidy.core.MixerController.set_volume>` instead.
        """
        deprecation.warn('core.playback.set_volume')
        return self.core.mixer.set_volume(volume)

    volume = deprecation.deprecated_property(get_volume, set_volume)
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
        deprecation.warn('core.playback.get_mute')
        return self.core.mixer.get_mute()

    def set_mute(self, mute):
        """
        .. deprecated:: 1.0
            Use :meth:`core.mixer.set_mute()
            <mopidy.core.MixerController.set_mute>` instead.
        """
        deprecation.warn('core.playback.set_mute')
        return self.core.mixer.set_mute(mute)

    mute = deprecation.deprecated_property(get_mute, set_mute)
    """
    .. deprecated:: 1.0
        Use :meth:`core.mixer.get_mute()
        <mopidy.core.MixerController.get_mute>` and
        :meth:`core.mixer.set_mute()
        <mopidy.core.MixerController.set_mute>` instead.
    """

    # Methods

    def _on_end_of_stream(self):
        self.set_state(PlaybackState.STOPPED)
        if self._current_tl_track:
            self._trigger_track_playback_ended(self.get_time_position())
        self._set_current_tl_track(None)

    def _on_stream_changed(self, uri):
        if self._last_position is None:
            position = self.get_time_position()
        else:
            # This code path handles the stop() case, uri should be none.
            position, self._last_position = self._last_position, None

        if self._pending_position is None:
            self._trigger_track_playback_ended(position)

        self._stream_title = None
        if self._pending_tl_track:
            self._set_current_tl_track(self._pending_tl_track)
            self._pending_tl_track = None

            if self._pending_position is None:
                self.set_state(PlaybackState.PLAYING)
                self._trigger_track_playback_started()
                seek_ok = False
                if self._start_at_position:
                    seek_ok = self.seek(self._start_at_position)
                    self._start_at_position = None
                if not seek_ok and self._start_paused:
                    self.pause()
                    self._start_paused = False
            else:
                self._seek(self._pending_position)

    def _on_position_changed(self, position):
        if self._pending_position is not None:
            self._trigger_seeked(self._pending_position)
            self._pending_position = None
            if self._start_paused:
                self._start_paused = False
                self.pause()

    def _on_about_to_finish_callback(self):
        """Callback that performs a blocking actor call to the real callback.

        This is passed to audio, which is allowed to call this code from the
        audio thread. We pass execution into the core actor to ensure that
        there is no unsafe access of state in core. This must block until
        we get a response.
        """
        self.core.actor_ref.ask({
            'command': 'pykka_call', 'args': tuple(), 'kwargs': {},
            'attr_path': ('playback', '_on_about_to_finish'),
        })

    def _on_about_to_finish(self):
        if self._state == PlaybackState.STOPPED:
            return

        # Unless overridden by other calls (e.g. next / previous / stop) this
        # will be the last position recorded until the track gets reassigned.
        # TODO: Check if case when track.length isn't populated needs to be
        # handled.
        self._last_position = self._current_tl_track.track.length

        pending = self.core.tracklist.eot_track(self._current_tl_track)
        # avoid endless loop if 'repeat' is 'true' and no track is playable
        # * 2 -> second run to get all playable track in a shuffled playlist
        count = self.core.tracklist.get_length() * 2

        while pending:
            backend = self._get_backend(pending)
            if backend:
                try:
                    if backend.playback.change_track(pending.track).get():
                        self._pending_tl_track = pending
                        break
                except Exception:
                    logger.exception('%s backend caused an exception.',
                                     backend.actor_ref.actor_class.__name__)

            self.core.tracklist._mark_unplayable(pending)
            pending = self.core.tracklist.eot_track(pending)
            count -= 1
            if not count:
                logger.info('No playable track in the list.')
                break

    def _on_tracklist_change(self):
        """
        Tell the playback controller that the current playlist has changed.

        Used by :class:`mopidy.core.TracklistController`.
        """
        if not self.core.tracklist.tl_tracks:
            self.stop()
            self._set_current_tl_track(None)
        elif self.get_current_tl_track() not in self.core.tracklist.tl_tracks:
            self._set_current_tl_track(None)

    def next(self):
        """
        Change to the next track.

        The current playback state will be kept. If it was playing, playing
        will continue. If it was paused, it will still be paused, etc.
        """
        state = self.get_state()
        current = self._pending_tl_track or self._current_tl_track
        # avoid endless loop if 'repeat' is 'true' and no track is playable
        # * 2 -> second run to get all playable track in a shuffled playlist
        count = self.core.tracklist.get_length() * 2

        while current:
            pending = self.core.tracklist.next_track(current)
            if self._change(pending, state):
                break
            else:
                self.core.tracklist._mark_unplayable(pending)
            # TODO: this could be needed to prevent a loop in rare cases
            # if current == pending:
            #     break
            current = pending
            count -= 1
            if not count:
                logger.info('No playable track in the list.')
                break

        # TODO return result?

    def pause(self):
        """Pause playback."""
        backend = self._get_backend(self.get_current_tl_track())
        # TODO: Wrap backend call in error handling.
        if not backend or backend.playback.pause().get():
            # TODO: switch to:
            # backend.track(pause)
            # wait for state change?
            self.set_state(PlaybackState.PAUSED)
            self._trigger_track_playback_paused()

    def play(self, tl_track=None, tlid=None):
        """
        Play the given track, or if the given tl_track and tlid is
        :class:`None`, play the currently active track.

        Note that the track **must** already be in the tracklist.

        :param tl_track: track to play
        :type tl_track: :class:`mopidy.models.TlTrack` or :class:`None`
        :param tlid: TLID of the track to play
        :type tlid: :class:`int` or :class:`None`
        """
        if sum(o is not None for o in [tl_track, tlid]) > 1:
            raise ValueError('At most one of "tl_track" and "tlid" may be set')

        tl_track is None or validation.check_instance(tl_track, models.TlTrack)
        tlid is None or validation.check_integer(tlid, min=1)

        if tl_track:
            deprecation.warn('core.playback.play:tl_track_kwarg', pending=True)

        if tl_track is None and tlid is not None:
            for tl_track in self.core.tracklist.get_tl_tracks():
                if tl_track.tlid == tlid:
                    break
            else:
                tl_track = None

        if tl_track is not None:
            # TODO: allow from outside tracklist, would make sense given refs?
            assert tl_track in self.core.tracklist.get_tl_tracks()
        elif tl_track is None and self.get_state() == PlaybackState.PAUSED:
            self.resume()
            return

        current = self._pending_tl_track or self._current_tl_track
        pending = tl_track or current or self.core.tracklist.next_track(None)
        # avoid endless loop if 'repeat' is 'true' and no track is playable
        # * 2 -> second run to get all playable track in a shuffled playlist
        count = self.core.tracklist.get_length() * 2

        while pending:
            if self._change(pending, PlaybackState.PLAYING):
                break
            else:
                self.core.tracklist._mark_unplayable(pending)
            current = pending
            pending = self.core.tracklist.next_track(current)
            count -= 1
            if not count:
                logger.info('No playable track in the list.')
                break

        # TODO return result?

    def _change(self, pending_tl_track, state):
        self._pending_tl_track = pending_tl_track

        if not pending_tl_track:
            self.stop()
            self._on_end_of_stream()  # pretend an EOS happened for cleanup
            return True

        backend = self._get_backend(pending_tl_track)
        if not backend:
            return False

        # This must happen before prepare_change gets called, otherwise the
        # backend flushes the information of the track.
        self._last_position = self.get_time_position()

        # TODO: Wrap backend call in error handling.
        backend.playback.prepare_change()

        try:
            if not backend.playback.change_track(pending_tl_track.track).get():
                return False
        except Exception:
            logger.exception('%s backend caused an exception.',
                             backend.actor_ref.actor_class.__name__)
            return False

        # TODO: Wrap backend calls in error handling.
        if state == PlaybackState.PLAYING:
            try:
                return backend.playback.play().get()
            except TypeError:
                # TODO: check by binding against underlying play method using
                # inspect and otherwise re-raise?
                logger.error('%s needs to be updated to work with this '
                             'version of Mopidy.', backend)
                return False
        elif state == PlaybackState.PAUSED:
            return backend.playback.pause().get()
        elif state == PlaybackState.STOPPED:
            # TODO: emit some event now?
            self._current_tl_track = self._pending_tl_track
            self._pending_tl_track = None
            return True

        raise Exception('Unknown state: %s' % state)

    def previous(self):
        """
        Change to the previous track.

        The current playback state will be kept. If it was playing, playing
        will continue. If it was paused, it will still be paused, etc.
        """
        self._previous = True
        state = self.get_state()
        current = self._pending_tl_track or self._current_tl_track
        # avoid endless loop if 'repeat' is 'true' and no track is playable
        # * 2 -> second run to get all playable track in a shuffled playlist
        count = self.core.tracklist.get_length() * 2

        while current:
            pending = self.core.tracklist.previous_track(current)
            if self._change(pending, state):
                break
            else:
                self.core.tracklist._mark_unplayable(pending)
            # TODO: this could be needed to prevent a loop in rare cases
            # if current == pending:
            #     break
            current = pending
            count -= 1
            if not count:
                logger.info('No playable track in the list.')
                break

        # TODO: no return value?

    def resume(self):
        """If paused, resume playing the current track."""
        if self.get_state() != PlaybackState.PAUSED:
            return
        backend = self._get_backend(self.get_current_tl_track())
        # TODO: Wrap backend call in error handling.
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
        # TODO: seek needs to take pending tracks into account :(
        validation.check_integer(time_position)

        if time_position < 0:
            logger.debug(
                'Client seeked to negative position. Seeking to zero.')
            time_position = 0

        if not self.core.tracklist.tracks:
            return False

        if self.get_state() == PlaybackState.STOPPED:
            self.play()

        # We need to prefer the still playing track, but if nothing is playing
        # we fall back to the pending one.
        tl_track = self._current_tl_track or self._pending_tl_track
        if tl_track and tl_track.track.length is None:
            return False

        if time_position < 0:
            time_position = 0
        elif time_position > tl_track.track.length:
            # TODO: GStreamer will trigger a about-to-finish for us, use that?
            self.next()
            return True

        # Store our target position.
        self._pending_position = time_position

        # Make sure we switch back to previous track if we get a seek while we
        # have a pending track.
        if self._current_tl_track and self._pending_tl_track:
            self._change(self._current_tl_track, self.get_state())
        else:
            return self._seek(time_position)

    def _seek(self, time_position):
        backend = self._get_backend(self.get_current_tl_track())
        if not backend:
            return False
        # TODO: Wrap backend call in error handling.
        return backend.playback.seek(time_position).get()

    def stop(self):
        """Stop playing."""
        if self.get_state() != PlaybackState.STOPPED:
            self._last_position = self.get_time_position()
            backend = self._get_backend(self.get_current_tl_track())
            # TODO: Wrap backend call in error handling.
            if not backend or backend.playback.stop().get():
                self.set_state(PlaybackState.STOPPED)

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
        if self.get_current_tl_track() is None:
            return

        logger.debug('Triggering track playback started event')
        tl_track = self.get_current_tl_track()
        self.core.tracklist._mark_playing(tl_track)
        self.core.history._add_track(tl_track.track)
        listener.CoreListener.send('track_playback_started', tl_track=tl_track)

    def _trigger_track_playback_ended(self, time_position_before_stop):
        tl_track = self.get_current_tl_track()
        if tl_track is None:
            return

        logger.debug('Triggering track playback ended event')

        if not self._previous:
            self.core.tracklist._mark_played(self._current_tl_track)
        self._previous = False

        # TODO: Use the lowest of track duration and position.
        listener.CoreListener.send(
            'track_playback_ended',
            tl_track=tl_track,
            time_position=time_position_before_stop)

    def _trigger_playback_state_changed(self, old_state, new_state):
        logger.debug('Triggering playback state change event')
        listener.CoreListener.send(
            'playback_state_changed',
            old_state=old_state, new_state=new_state)

    def _trigger_seeked(self, time_position):
        # TODO: Trigger this from audio events?
        logger.debug('Triggering seeked event')
        listener.CoreListener.send('seeked', time_position=time_position)

    def _save_state(self):
        return models.PlaybackState(
            tlid=self.get_current_tlid(),
            time_position=self.get_time_position(),
            state=self.get_state())

    def _load_state(self, state, coverage):
        if state and 'play-last' in coverage and state.tlid is not None:
            if state.state == PlaybackState.PAUSED:
                self._start_paused = True
            if state.state in (PlaybackState.PLAYING, PlaybackState.PAUSED):
                self._start_at_position = state.time_position
                self.play(tlid=state.tlid)
