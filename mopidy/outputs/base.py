class BaseOutput(object):
    """
    Base class for audio outputs.
    """

    def start(self):
        """Start the output."""
        pass

    def destroy(self):
        """Destroy the output."""
        pass

    def process_message(self, message):
        """Process messages with the output as destination."""
        raise NotImplementedError
