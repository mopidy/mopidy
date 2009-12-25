import asyncore
import logging
import socket
import sys

from mopidy import settings
from mopidy.session import MpdSession
from mopidy.backends.spotify import SpotifyBackend

logger = logging.getLogger(u'server')

class MpdServer(asyncore.dispatcher):
    def __init__(self, session_class=MpdSession, backend=SpotifyBackend):
        asyncore.dispatcher.__init__(self)
        self.session_class = session_class
        self.backend = SpotifyBackend()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((settings.MPD_SERVER_HOSTNAME, settings.MPD_SERVER_PORT))
        self.listen(1)

    def handle_accept(self):
        (client_socket, client_address) = self.accept()
        logger.info(u'Connection from: [%s]:%s', *client_address)
        self.session_class(self, client_socket, client_address,
            backend=self.backend)

    def handle_close(self):
        self.close()

    def do_kill(self):
        logger.info(u'Received "kill". Shutting down.')
        self.handle_close()
        sys.exit(0)

