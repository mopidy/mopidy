import logging

from mopidy.frontends.mpd.dispatcher import MpdDispatcher
from mopidy.frontends.mpd.process import MpdProcess
from mopidy.utils.process import unpickle_connection

logger = logging.getLogger('mopidy.frontends.mpd')

class MpdFrontend(object):
    """
    The MPD frontend.

    **Settings:**

    - :attr:`mopidy.settings.MPD_SERVER_HOSTNAME`
    - :attr:`mopidy.settings.MPD_SERVER_PORT`
    """

    def __init__(self, core_queue, backend):
        self.core_queue = core_queue
        self.process = None
        self.dispatcher = MpdDispatcher(backend)

    def start(self):
        """Starts the MPD server."""
        self.process = MpdProcess(self.core_queue)
        self.process.start()

    def process_message(self, message):
        """
        Processes messages with the MPD frontend as destination.

        :param message: the message
        :type message: dict
        """
        assert message['to'] == 'frontend', \
            u'Message recipient must be "frontend".'
        if message['command'] == 'mpd_request':
            response = self.dispatcher.handle_request(message['request'])
            connection = unpickle_connection(message['reply_to'])
            connection.send(response)
        else:
            logger.warning(u'Cannot handle message: %s', message)
