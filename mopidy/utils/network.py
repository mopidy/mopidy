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

class BaseHandler(object):
    """Buffered lined based client, subclass for use."""

    #: Line terminator to use in parse_line, can be overridden by subclasses.
    terminator = '\n'

    def __init__(self, (sock, addr)):
        logger.debug('Established connection from %s', addr)

        self.sock, self.addr = sock, addr
        self.receiver = None
        self.sender = None
        self.recv_buffer = ''
        self.send_buffer = ''

        self.sock.setblocking(0)
        self.add_recv_watch()

    def add_recv_watch(self):
        """Register recv and error handling of socket."""
        if self.receiver is None:
            self.receiver = gobject.io_add_watch(self.sock.fileno(), gobject.IO_IN
                | gobject.IO_ERR | gobject.IO_HUP, self.handle)

    def clear_recv_watch(self):
        if self.receiver is not None:
            gobject.source_remove(self.receiver)
            self.receiver = None

    def add_send_watch(self):
        """Register send handling if it has not already been done."""
        if self.sender is None:
            self.sender = gobject.io_add_watch(self.sock.fileno(),
                gobject.IO_OUT, self.handle)

    def clear_send_watch(self):
        """Remove send watcher if it is set."""
        if self.sender is not None:
            gobject.source_remove(self.sender)
            self.sender = None

    def handle(self, fd, flags):
        """Dispatch based on current flags."""
        if flags & (gobject.IO_ERR | gobject.IO_HUP):
            return self.close()
        if flags & gobject.IO_IN:
            return self.io_in()
        if flags & gobject.IO_OUT:
            return self.io_out()
        logger.error('Unknown flag: %s', flags)
        return False

    def io_in(self):
        """Record any incoming data to buffer and parse lines."""
        data = self.sock.recv(1024)
        self.recv_buffer += data # XXX limit buffer size?
        if data:
            return self.parse_lines()
        else:
            return self.close()

    def io_out(self):
        """Send as much of outgoing buffer as possible."""
        if self.send_buffer:
            sent = self.sock.send(self.send_buffer)
            self.send_buffer = self.send_buffer[sent:]
        if not self.send_buffer:
            self.clear_send_watch()
        return True

    def close(self):
        """Close connection."""
        logger.debug('Closing connection from %s', self.addr)
        self.clear_send_watch()
        self.sock.close()
        return False

    def release(self):
        """Forget about socket so that other loop can take over FD.

        Note that other code will still need to keep a ref to the socket in
        order to prevent GC cleanup closing it.
        """
        self.clear_recv_watch()
        self.clear_send_watch()
        return self.sock

    def send(self, data):
        """Add raw data to send to outbound buffer."""
        self.add_send_watch()
        self.send_buffer += data # XXX limit buffer size?

    def recv(self, line):
        """Recv one and one line of request. Must be sub-classed."""
        raise NotImplementedError

    def parse_lines(self):
        """Parse lines by splitting at terminator."""
        while self.terminator in self.recv_buffer:
            line, self.recv_buffer = self.recv_buffer.split(self.terminator, 1)
            self.recv(line)
        return True

class EchoHandler(BaseHandler):
    """Basic handler used for debuging of Listener and Handler code itself."""
    def recv(self, line):
        print repr(line)
        self.send(line)

class Listener(object):
    """Setup listener and register it with gobject loop."""
    def __init__(self, addr, handler=EchoHandler):
        self.handler = handler
        self.sock = create_socket()
        self.sock.setblocking(0)
        self.sock.bind(addr)
        self.sock.listen(5)

        gobject.io_add_watch(self.sock.fileno(), gobject.IO_IN, self.handle)
        logger.debug('Listening on %s using %s', addr, self.handler)

    def handle(self, fd, flags):
        self.handler(self.sock.accept())
        return True

