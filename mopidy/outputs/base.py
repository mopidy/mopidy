class BaseOutput(object):
    """
    Base class for audio outputs.
    """

    def play_uri(self, uri):
        """
        Play URI.

        *MUST be implemented by subclass.*

        :param uri: the URI to play
        :type uri: string
        :rtype: :class:`True` if successful, else :class:`False`
        """
        raise NotImplementedError

    def deliver_data(self, capabilities, data):
        """
        Deliver audio data to be played.

        *MUST be implemented by subclass.*

        :param capabilities: a GStreamer capabilities string
        :type capabilities: string
        """
        raise NotImplementedError

    def end_of_data_stream(self):
        """
        Signal that the last audio data has been delivered.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def get_position(self):
        """
        Get position in milliseconds.

        *MUST be implemented by subclass.*

        :rtype: int
        """
        raise NotImplementedError

    def set_position(self, position):
        """
        Set position in milliseconds.

        *MUST be implemented by subclass.*

        :param position: the position in milliseconds
        :type volume: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        raise NotImplementedError

    def set_state(self, state):
        """
        Set playback state.

        *MUST be implemented by subclass.*

        :param state: the state
        :type state: string
        :rtype: :class:`True` if successful, else :class:`False`
        """
        raise NotImplementedError

    def get_volume(self):
        """
        Get volume level for software mixer.

        *MUST be implemented by subclass.*

        :rtype: int in range [0..100]
        """
        raise NotImplementedError

    def set_volume(self, volume):
        """
        Set volume level for software mixer.

        *MUST be implemented by subclass.*

        :param volume: the volume in the range [0..100]
        :type volume: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        raise NotImplementedError
