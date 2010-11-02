class BaseFrontend(object):
    """
    Base class for frontends.

    :param core_queue: queue for messaging the core
    :type core_queue: :class:`multiprocessing.Queue`
    :param backend: the backend
    :type backend: :class:`mopidy.backends.base.BaseBackend`
    """

    def __init__(self, core_queue, backend):
        self.core_queue = core_queue
        self.backend = backend

    def start(self):
        """
        Start the frontend.

        *MAY be implemented by subclass.*
        """
        pass

    def destroy(self):
        """
        Destroy the frontend.

        *MAY be implemented by subclass.*
        """
        pass

    def process_message(self, message):
        """
        Process messages for the frontend.

        *MUST be implemented by subclass.*

        :param message: the message
        :type message: dict
        """
        raise NotImplementedError
