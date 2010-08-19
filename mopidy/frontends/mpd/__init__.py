from mopidy.frontends.mpd.dispatcher import MpdDispatcher
from mopidy.frontends.mpd.server import MpdServer

class MpdFrontend(object):
    """
    The MPD frontend.
    """

    def __init__(self):
        self.server = None
        self.dispatcher = None

    def start_server(self, core_queue):
        """
        Starts the MPD server.

        :param core_queue: the core queue
        :type core_queue: :class:`multiprocessing.Queue`
        """
        self.server = MpdServer(core_queue)
        self.server.start()

    def create_dispatcher(self, backend):
        """
        Creates a dispatcher for MPD requests.

        :param backend: the backend
        :type backend: :class:`mopidy.backends.base.BaseBackend`
        :rtype: :class:`mopidy.frontends.mpd.dispatcher.MpdDispatcher`
        """

        self.dispatcher = MpdDispatcher(backend)
        return self.dispatcher
