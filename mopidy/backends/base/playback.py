import time

from mopidy.core.playback import PlaybackState


class BasePlaybackProvider(object):
    """
    :param backend: the backend
    :type backend: :class:`mopidy.backends.base.Backend`
    """

    pykka_traversable = True

    def __init__(self, backend):
        self.backend = backend

        self._play_time_accumulated = 0
        self._play_time_started = 0

    def pause(self):
        """
        Pause playback.

        *MAY be reimplemented by subclass.*

        :rtype: :class:`True` if successful, else :class:`False`
        """
        return self.backend.audio.pause_playback().get()

    def play(self, track):
        """
        Play given track.

        *MAY be reimplemented by subclass.*

        :param track: the track to play
        :type track: :class:`mopidy.models.Track`
        :rtype: :class:`True` if successful, else :class:`False`
        """
        self.backend.audio.prepare_change()
        self.backend.audio.set_uri(track.uri).get()
        return self.backend.audio.start_playback().get()

    def resume(self):
        """
        Resume playback at the same time position playback was paused.

        *MAY be reimplemented by subclass.*

        :rtype: :class:`True` if successful, else :class:`False`
        """
        return self.backend.audio.start_playback().get()

    def seek(self, time_position):
        """
        Seek to a given time position.

        *MAY be reimplemented by subclass.*

        :param time_position: time position in milliseconds
        :type time_position: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        return self.backend.audio.set_position(time_position).get()

    def stop(self):
        """
        Stop playback.

        *MAY be reimplemented by subclass.*

        :rtype: :class:`True` if successful, else :class:`False`
        """
        return self.backend.audio.stop_playback().get()

    def get_time_position(self):
        """
        Get the current time position in milliseconds.

        *MAY be reimplemented by subclass.*

        :rtype: int
        """
        return self.backend.audio.get_position().get()

    def get_volume(self):
        """
        Get current volume

        *MAY be reimplemented by subclass.*

        :rtype: int [0..100] or :class:`None`
        """
        return self.backend.audio.get_volume().get()

    def set_volume(self, volume):
        """
        Get current volume

        *MAY be reimplemented by subclass.*

        :param: volume
        :type volume: int [0..100]
        """
        self.backend.audio.set_volume(volume)

    def wall_clock_based_time_position(self):
        """
        Helper method that tracks track time position using the wall clock.

        To use this helper you must call the helper from your implementation of
        :meth:`get_time_position` and return its return value.

        :rtype: int
        """
        state = self.backend.playback.state
        if state == PlaybackState.PLAYING:
            time_since_started = (self._wall_time() -
                self._play_time_started)
            return self._play_time_accumulated + time_since_started
        elif state == PlaybackState.PAUSED:
            return self._play_time_accumulated
        elif state == PlaybackState.STOPPED:
            return 0

    def update_play_time_on_play(self):
        self._play_time_accumulated = 0
        self._play_time_started = self._wall_time()

    def update_play_time_on_pause(self):
        time_since_started = self._wall_time() - self._play_time_started
        self._play_time_accumulated += time_since_started

    def update_play_time_on_resume(self):
        self._play_time_started = self._wall_time()

    def update_play_time_on_seek(self, time_position):
        self._play_time_started = self._wall_time()
        self._play_time_accumulated = time_position

    def _wall_time(self):
        return int(time.time() * 1000)
