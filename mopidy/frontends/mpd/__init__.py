import logging

from mopidy.frontends.base import BaseFrontend
from mopidy.frontends.mpd.dispatcher import MpdDispatcher
from mopidy.frontends.mpd.thread import MpdThread
from mopidy.utils.process import unpickle_connection

logger = logging.getLogger('mopidy.frontends.mpd')

class MpdFrontend(BaseFrontend):
    """
    The MPD frontend.

    **Settings:**

    - :attr:`mopidy.settings.MPD_SERVER_HOSTNAME`
    - :attr:`mopidy.settings.MPD_SERVER_PORT`
    """

    def __init__(self, *args, **kwargs):
        super(MpdFrontend, self).__init__(*args, **kwargs)
        self.thread = None
        self.dispatcher = MpdDispatcher(self.backend)

    def start(self):
        """Starts the MPD server."""
        self.thread = MpdThread(self.core_queue)
        self.thread.start()

    def destroy(self):
        """Destroys the MPD server."""
        self.thread.destroy()

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
            pass # Ignore messages for other frontends
