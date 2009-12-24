import asyncore
import logging
import socket
import sys

from mopidy import settings
from mopidy.session import MpdSession

logger = logging.getLogger(u'server')

class MpdServer(asyncore.dispatcher):
    def __init__(self, handler_class=MpdSession):
        asyncore.dispatcher.__init__(self)
        self.handler_class = handler_class
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((settings.MPD_SERVER_HOSTNAME, settings.MPD_SERVER_PORT))
        self.listen(1)

    def handle_accept(self):
        (client_socket, client_address) = self.accept()
        logger.info(u'Connection from: [%s]:%s', *client_address)
        self.handler_class(self, client_socket, client_address)

    def handle_close(self):
        self.close()

    def do_kill(self):
        logger.info('Received "kill". Shutting down.')
        self.handle_close()
        sys.exit(0)

