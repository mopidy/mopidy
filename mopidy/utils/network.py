import logging
import re
import socket
import gobject

logger = logging.getLogger('mopidy.utils.server')

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

#: Boolean value that indicates if creating an IPv6 socket will succeed.
has_ipv6 = _try_ipv6_socket()

def create_socket():
    """Create a TCP socket with or without IPv6 depending on system support"""
    if has_ipv6:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        # Explicitly configure socket to work for both IPv4 and IPv6
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock

def format_hostname(hostname):
    """Format hostname for display."""
    if (has_ipv6 and re.match('\d+.\d+.\d+.\d+', hostname) is not None):
        hostname = '::ffff:%s' % hostname
    return hostname

class Listener(object):
    """Setup listener and register it with gobject loop."""
    def __init__(self, addr, session):
        self.session = session
        self.sock = create_socket()
        self.sock.setblocking(0)
        self.sock.bind(addr)
        self.sock.listen(5)

        gobject.io_add_watch(self.sock.fileno(), gobject.IO_IN, self.handle)
        logger.debug('Listening on %s using %s', addr, self.session)

    def handle(self, fd, flags):
        sock, addr = self.sock.accept()
        logger.debug('Got connection from %s', addr)
        self.session.start(sock, addr)
        return True

