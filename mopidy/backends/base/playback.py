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

        *MUST be implemented by subclass.*

        :rtype: :class:`True` if successful, else :class:`False`
        """
        raise NotImplementedError

    def play(self, track):
        """
        Play given track.

        *MUST be implemented by subclass.*

        :param track: the track to play
        :type track: :class:`mopidy.models.Track`
        :rtype: :class:`True` if successful, else :class:`False`
        """
        raise NotImplementedError

    def resume(self):
        """
        Resume playback at the same time position playback was paused.

        *MUST be implemented by subclass.*

        :rtype: :class:`True` if successful, else :class:`False`
        """
        raise NotImplementedError

    def seek(self, time_position):
        """
        Seek to a given time position.

        *MUST be implemented by subclass.*

        :param time_position: time position in milliseconds
        :type time_position: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        raise NotImplementedError

    def stop(self):
        """
        Stop playback.

        *MUST be implemented by subclass.*

        :rtype: :class:`True` if successful, else :class:`False`
        """
        raise NotImplementedError

    def get_volume(self):
        """
        Get current volume

        *MUST be implemented by subclass.*

        :rtype: int [0..100] or :class:`None`
        """
        raise NotImplementedError

    def set_volume(self, volume):
        """
        Get current volume

        *MUST be implemented by subclass.*

        :param: volume
        :type volume: int [0..100]
        """
        raise NotImplementedError
