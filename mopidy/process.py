import logging
import multiprocessing
import sys

from mopidy import settings
from mopidy.utils import get_class, unpickle_connection

logger = logging.getLogger('mopidy.process')

class CoreProcess(multiprocessing.Process):
    def __init__(self, core_queue):
        multiprocessing.Process.__init__(self)
        self.core_queue = core_queue

    def run(self):
        try:
            self._setup()
            while True:
                message = self.core_queue.get()
                self._process_message(message)
        except KeyboardInterrupt:
            logger.info(u'Interrupted by user')
            sys.exit(0)

    def _setup(self):
        self._backend = get_class(settings.BACKENDS[0])(
            core_queue=self.core_queue)
        self._frontend = get_class(settings.FRONTEND)(backend=self._backend)

    def _process_message(self, message):
        if message['command'] == 'mpd_request':
            response = self._frontend.handle_request(message['request'])
            connection = unpickle_connection(message['reply_to'])
            connection.send(response)
        elif message['command'] == 'end_of_track':
            self._backend.playback.end_of_track_callback()
        else:
            logger.warning(u'Cannot handle message: %s', message)
