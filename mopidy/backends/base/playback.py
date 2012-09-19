class BasePlaybackProvider(object):
    """
    :param backend: the backend
    :type backend: :class:`mopidy.backends.base.Backend`
    """

    pykka_traversable = True

    def __init__(self, backend):
        self.backend = backend

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
