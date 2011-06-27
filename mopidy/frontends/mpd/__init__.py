import asyncore
import logging

from pykka.actor import ThreadingActor

from mopidy.frontends.mpd.server import MpdServer
from mopidy.utils.process import BaseThread

logger = logging.getLogger('mopidy.frontends.mpd')

class MpdFrontend(ThreadingActor):
    """
    The MPD frontend.

    **Dependencies:**

    - None

    **Settings:**

    - :attr:`mopidy.settings.MPD_SERVER_HOSTNAME`
    - :attr:`mopidy.settings.MPD_SERVER_PORT`
    - :attr:`mopidy.settings.MPD_SERVER_PASSWORD`
    """

    def __init__(self):
        self._thread = None

    def on_start(self):
        self._thread = MpdThread()
        self._thread.start()

    def on_receive(self, message):
        pass # Ignore any messages


class MpdThread(BaseThread):
    def __init__(self):
        super(MpdThread, self).__init__()
        self.name = u'MpdThread'

    def run_inside_try(self):
        logger.debug(u'Starting MPD server thread')
        server = MpdServer()
        server.start()
        asyncore.loop()
