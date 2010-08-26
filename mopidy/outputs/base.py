class BaseOutput(object):
    """
    Base class for audio outputs.
    """

    def __init__(self, core_queue):
        self.core_queue = core_queue

    def start(self):
        """Start the output."""
        pass

    def destroy(self):
        """Destroy the output."""
        pass

    def process_message(self, message):
        """Process messages with the output as destination."""
        raise NotImplementedError

    def play_uri(self, uri):
        """
        Play URI.

        :param uri: the URI to play
        :type uri: string
        :rtype: :class:`True` if successful, else :class:`False`
        """
        raise NotImplementedError

    def deliver_data(self, capabilities, data):
        """
        Deliver audio data to be played.

        :param capabilities: a GStreamer capabilities string
        :type capabilities: string
        """
        raise NotImplementedError

    def end_of_data_stream(self):
        """Signal that the last audio data has been delivered."""
        raise NotImplementedError

    def get_position(self):
        """
        Get position in milliseconds.

        :rtype: int
        """
        raise NotImplementedError

    def set_position(self, position):
        """
        Set position in milliseconds.

        :param position: the position in milliseconds
        :type volume: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        raise NotImplementedError

    def set_state(self, state):
        """
        Set playback state.

        :param state: the state
        :type state: string
        :rtype: :class:`True` if successful, else :class:`False`
        """
        raise NotImplementedError

    def get_volume(self):
        """
        Get volume level for software mixer.

        :rtype: int in range [0..100]
        """
        raise NotImplementedError

    def set_volume(self, volume):
        """
        Set volume level for software mixer.

        :param volume: the volume in the range [0..100]
        :type volume: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        raise NotImplementedError
