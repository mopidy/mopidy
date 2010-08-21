import asyncore
import logging

from mopidy.frontends.mpd.server import MpdServer
from mopidy.utils.process import BaseProcess

logger = logging.getLogger('mopidy.frontends.mpd.process')

class MpdProcess(BaseProcess):
    def __init__(self, core_queue):
        super(MpdProcess, self).__init__(name='MpdProcess')
        self.core_queue = core_queue

    def run_inside_try(self):
        logger.debug(u'Starting MPD server process')
        server = MpdServer(self.core_queue)
        server.start()
        asyncore.loop()
