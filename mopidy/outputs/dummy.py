from mopidy.outputs.base import BaseOutput

class DummyOutput(BaseOutput):
    """
    Audio output used for testing.
    """

    #: For testing. :class:`True` if :meth:`start` has been called.
    start_called = False

    #: For testing. :class:`True` if :meth:`destroy` has been called.
    destroy_called = False

    #: For testing. Contains all messages :meth:`process_message` has received.
    messages = []

    def start(self):
        self.start_called = True

    def destroy(self):
        self.destroy_called = True

    def process_message(self, message):
        self.messages.append(message)
