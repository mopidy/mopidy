import logging
import multiprocessing

from mopidy import get_class, settings, unpickle_connection

logger = logging.getLogger('mopidy.core')

class CoreProcess(multiprocessing.Process):
    def __init__(self, core_queue):
        multiprocessing.Process.__init__(self)
        self.core_queue = core_queue

    def run(self):
        backend = get_class(settings.BACKENDS[0])()
        frontend = get_class(settings.FRONTEND)(backend=backend)
        while True:
            message = self.core_queue.get()
            if message['command'] == 'mpd_request':
                response = frontend.handle_request(message['request'])
                connection = unpickle_connection(message['reply_to'])
                connection.send(response)
            else:
                logger.warning(u'Cannot handle message: %s', message)
