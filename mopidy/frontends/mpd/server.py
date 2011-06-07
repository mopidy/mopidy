import asyncore
import logging
import sys

from mopidy import settings
from mopidy.utils import network
from .session import MpdSession

logger = logging.getLogger('mopidy.frontends.mpd.server')

class MpdServer(asyncore.dispatcher):
    """
    The MPD server. Creates a :class:`mopidy.frontends.mpd.session.MpdSession`
    for each client connection.
    """

    def __init__(self):
        asyncore.dispatcher.__init__(self)

    def start(self):
        """Start MPD server."""
        try:
            self.socket = network.create_socket()
            hostname = network.format_hostname(settings.MPD_SERVER_HOSTNAME)
            port = settings.MPD_SERVER_PORT
            logger.debug(u'MPD server is binding to [%s]:%s', hostname, port)
            self.bind((hostname, port))
            self.listen(1)
            logger.info(u'MPD server running at [%s]:%s', hostname, port)
        except IOError, e:
            logger.error(u'MPD server startup failed: %s' %
                str(e).decode('utf-8'))
            sys.exit(1)

    def handle_accept(self):
        """Called by asyncore when a new client connects."""
        (client_socket, client_socket_address) = self.accept()
        logger.info(u'MPD client connection from [%s]:%s',
            client_socket_address[0], client_socket_address[1])
        MpdSession(self, client_socket, client_socket_address)

    def handle_close(self):
        """Called by asyncore when the socket is closed."""
        self.close()
