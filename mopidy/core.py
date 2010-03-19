import logging
import multiprocessing

from mopidy import get_class, settings, unpickle_connection

logger = logging.getLogger('mopidy.core')

class CoreProcess(multiprocessing.Process):
    def __init__(self, core_queue=None, main_queue=None, server_queue=None):
        multiprocessing.Process.__init__(self)
        self.queue = core_queue
        self.main_queue = main_queue
        self.server_queue = server_queue

    def run(self):
        backend = get_class(settings.BACKENDS[0])()
        frontend = get_class(settings.FRONTEND)(backend=backend)
        self.main_queue.put({'command': 'core_ready'})
        while True:
            message = self.queue.get()
            if message['command'] == 'mpd_request':
                response = frontend.handle_request(message['request'])
                connection = unpickle_connection(message['reply_to'])
                connection.send(response)
            else:
                logger.warning(u'Cannot handle message: %s', message)
