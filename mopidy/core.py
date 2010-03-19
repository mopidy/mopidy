import logging
from multiprocessing import Process, Queue

from mopidy import get_class, settings

logger = logging.getLogger('mopidy.core')

class CoreProcess(Process):
    def __init__(self, core_queue=None, main_queue=None, server_queue=None):
        Process.__init__(self)
        self.queue = core_queue
        self.main_queue = main_queue
        self.server_queue = server_queue

    def run(self):
        self._setup()
        while True:
            message = self.queue.get()
            # TODO Do something with the message

    def _setup(self):
        self.backend = get_class(settings.BACKENDS[0])()
        self.main_queue.put({'command': 'core_ready'})
