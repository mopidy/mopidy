import asyncore
import logging
import re
import socket
import sys

from mopidy import settings
from .session import MpdSession

logger = logging.getLogger('mopidy.frontends.mpd.server')

def _try_ipv6_socket():
    """Determine if system really supports IPv6"""
    if not socket.has_ipv6:
        return False
    try:
        socket.socket(socket.AF_INET6).close()
        return True
    except IOError, e:
        logger.debug(u'Platform supports IPv6, but socket '
            'creation failed, disabling: %s', e)
    return False

has_ipv6 = _try_ipv6_socket()

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
            if has_ipv6:
                self.create_socket(socket.AF_INET6, socket.SOCK_STREAM)
                # Explicitly configure socket to work for both IPv4 and IPv6
                self.socket.setsockopt(
                    socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            else:
                self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.set_reuse_addr()
            hostname = self._format_hostname(settings.MPD_SERVER_HOSTNAME)
            port = settings.MPD_SERVER_PORT
            logger.debug(u'MPD server is binding to [%s]:%s', hostname, port)
            self.bind((hostname, port))
            self.listen(1)
            logger.info(u'MPD server running at [%s]:%s',
                self._format_hostname(settings.MPD_SERVER_HOSTNAME),
                settings.MPD_SERVER_PORT)
        except IOError, e:
            logger.error('MPD server startup failed: %s' % e)
            sys.exit(1)

    def handle_accept(self):
        """Handle new client connection."""
        (client_socket, client_socket_address) = self.accept()
        logger.info(u'MPD client connection from [%s]:%s',
            client_socket_address[0], client_socket_address[1])
        MpdSession(self, client_socket, client_socket_address).start()

    def handle_close(self):
        """Handle end of client connection."""
        self.close()

    def _format_hostname(self, hostname):
        if (has_ipv6
            and re.match('\d+.\d+.\d+.\d+', hostname) is not None):
            hostname = '::ffff:%s' % hostname
        return hostname
