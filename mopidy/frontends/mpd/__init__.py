import asyncore
import logging

from pykka.actor import ThreadingActor

from mopidy.frontends.base import BaseFrontend
from mopidy.frontends.mpd.server import MpdServer
from mopidy.utils.process import BaseThread

logger = logging.getLogger('mopidy.frontends.mpd')

class MpdFrontend(ThreadingActor, BaseFrontend):
    """
    The MPD frontend.

    **Settings:**

    - :attr:`mopidy.settings.MPD_SERVER_HOSTNAME`
    - :attr:`mopidy.settings.MPD_SERVER_PASSWORD`
    - :attr:`mopidy.settings.MPD_SERVER_PORT`
    """

    def __init__(self):
        # TODO-PYKKA: Do setup after actor starts?
        self._thread = MpdThread()
        self._thread.start()

    def destroy(self):
        """Destroys the MPD server."""
        self._thread.destroy()


class MpdThread(BaseThread):
    def __init__(self):
        super(BaseThread, self).__init__()
        self.name = u'MpdThread'

    def run_inside_try(self):
        logger.debug(u'Starting MPD server thread')
        server = MpdServer()
        server.start()
        asyncore.loop()
