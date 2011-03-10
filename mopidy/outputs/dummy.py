from pykka.actor import ThreadingActor

from mopidy.outputs.base import BaseOutput

class DummyOutput(ThreadingActor, BaseOutput):
    """
    Audio output used for testing.
    """

    # pylint: disable = R0902
    # Too many instance attributes (9/7)

    #: For testing. Contains the last URI passed to :meth:`play_uri`.
    uri = None

    #: For testing. Contains the last capabilities passed to
    #: :meth:`deliver_data`.
    capabilities = None

    #: For testing. Contains the last data passed to :meth:`deliver_data`.
    data = None

    #: For testing. :class:`True` if :meth:`end_of_data_stream` has been
    #: called.
    end_of_data_stream_called = False

    #: For testing. Contains the current position.
    position = 0

    #: For testing. Contains the current state.
    state = 'NULL'

    #: For testing. Contains the current volume.
    volume = 100

    def play_uri(self, uri):
        self.uri = uri
        return True

    def deliver_data(self, capabilities, data):
        self.capabilities = capabilities
        self.data = data

    def end_of_data_stream(self):
        self.end_of_data_stream_called = True

    def get_position(self):
        return self.position

    def set_position(self, position):
        self.position = position
        return True

    def set_state(self, state):
        self.state = state
        return True

    def get_volume(self):
        return self.volume

    def set_volume(self, volume):
        self.volume = volume
        return True
