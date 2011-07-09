import errno
import gobject
import logging
import re
import socket
import threading

from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry

from mopidy.utils.log import indent

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

class Server(object):
    """Setup listener and register it with gobject's event loop."""

    def __init__(self, host, port, protocol, max_connections=15):
        self.protocol = protocol
        self.max_connections = max_connections
        self.listener = create_socket()
        self.listener.setblocking(False)
        self.listener.bind((host, port))
        self.listener.listen(1)

        gobject.io_add_watch(
            self.listener.fileno(), gobject.IO_IN, self.handle_accept)
        logger.debug(u'Listening on [%s]:%s using %s as protocol handler',
            host, port, self.protocol.__name__)

    def handle_accept(self, fd, flags):
        try:
            sock, addr = self.listener.accept()
        except socket.error as e:
            if e.errno in (errno.EAGAIN, errno.EINTR):
                return True # i.e. retry
            raise

        num_connections = len(ActorRegistry.get_by_class(self.protocol))
        if self.max_connections and num_connections >= self.max_connections:
            logger.warning(u'Rejected connection from [%s]:%s', addr[0], addr[1])
            try:
                sock.close()
            except socket.error:
                pass
            return True

        self.protocol.start(sock, addr)
        return True


class LineProtocol(ThreadingActor):
    """
    Base class for handling line based protocols.

    Takes care of receiving new data from server's client code, decoding and
    then splitting data along line boundaries.
    """

    #: What terminator to use to split lines.
    terminator = '\n'

    #: What encoding to expect incomming data to be in, can be :class:`None`.
    encoding = 'utf-8'

    #: How long to wait before disconnecting client due to inactivity in
    #: seconds.
    timeout = 30

    def __init__(self, sock, addr):
        sock.setblocking(False)

        self.sock = sock
        self.host, self.port = addr[:2] # IPv6 has larger addr
        self.send_lock = threading.Lock()
        self.recv_buffer = ''
        self.send_buffer = ''
        self.terminator_re = re.compile(self.terminator)
        self.send_id = None
        self.recv_id = None
        self.timeout_id = None

        self.sock.setblocking(False)

        self.enable_recv()
        self.enable_timeout()

    def on_line_received(self, line):
        """
        Called whenever a new line is found.

        Should be implemented by subclasses.
        """
        raise NotImplemented

    def on_receive(self, message):
        """Handle messages with new data from server."""
        if 'received' not in message:
            return

        self.disable_timeout()
        self.log_raw_data(message['received'])

        for line in self.parse_lines(message['received']):
            line = self.decode(line)
            self.log_request(line)
            self.on_line_received(line)

        self.enable_timeout()

    def on_stop(self):
        """Ensure that cleanup when actor stops."""
        self.disable_timeout()
        self.disable_recv()
        self.disable_send()
        try:
            self.sock.close()
        except socket.error:
            pass

    def disable_timeout(self):
        """Deactivate timeout mechanism."""
        if self.timeout_id is not None:
            gobject.source_remove(self.timeout_id)
            self.timeout_id = None

    def disable_recv(self):
        """Deactivate recv mechanism."""
        if self.recv_id is not None:
            gobject.source_remove(self.recv_id)
            self.recv_id = None

    def disable_send(self):
        """Deactivate send mechanism."""
        if self.send_id:
            gobject.source_remove(self.send_id)
            self.send_id = None

    def enable_recv(self):
        """Reactivate recv mechanism."""
        if self.recv_id is None:
            self.recv_id = gobject.io_add_watch(self.sock.fileno(), gobject.IO_IN |
                gobject.IO_ERR | gobject.IO_HUP, self._recv)

    def enable_send(self):
        """Reactivate send mechanism."""
        if self.send_id is None:
            self.send_id = gobject.io_add_watch(self.sock.fileno(),
                gobject.IO_OUT | gobject.IO_ERR | gobject.IO_HUP, self._send)

    def enable_timeout(self):
        """Reactivate timeout mechanism."""
        self.disable_timeout()
        self.timeout_id = gobject.timeout_add_seconds(self.timeout,
            self._timeout)

    def parse_lines(self, new_data=None):
        """Consume new data and yield any lines found."""
        if new_data:
            self.recv_buffer += new_data
        while self.terminator_re.search(self.recv_buffer):
            line, self.recv_buffer = self.terminator_re.split(
                self.recv_buffer, 1)
            yield line

    def log_raw_data(self, data):
        """
        Log raw data from event loop for debug purposes.

        Can be overridden by subclasses to change logging behaviour.
        """
        logger.debug(u'Got %s from event loop in %s',
            repr(data), self.actor_urn)

    def log_request(self, request):
        """
        Log request for debug purposes.

        Can be overridden by subclasses to change logging behaviour.
        """
        logger.debug(u'Request from [%s]:%s to %s: %s',
            self.host, self.port, self.actor_urn, indent(request))

    def log_response(self, response):
        """
        Log response for debug purposes.

        Can be overridden by subclasses to change logging behaviour.
        """
        logger.debug(u'Response to [%s]:%s from %s: %s',
            self.host, self.port, self.actor_urn, indent(response))

    def log_error(self, error):
        """
        Log error for debug purposes.

        Can be overridden by subclasses to change logging behaviour.
        """
        logger.warning(u'Problem with connection to [%s]:%s in %s: %s',
            self.host, self.port, self.actor_urn, error)

    def log_timeout(self):
        """
        Log timeout for debug purposes.

        Can be overridden by subclasses to change logging behaviour.
        """
        logger.debug(u'Closing connection to [%s]:%s in %s due to timeout.',
            self.host, self.port, self.actor_urn)

    def encode(self, line):
        """
        Handle encoding of line.

        Can be overridden by subclasses to change encoding behaviour.
        """
        if self.encoding:
            return line.encode(self.encoding)
        return line

    def decode(self, line):
        """
        Handle decoding of line.

        Can be overridden by subclasses to change decoding behaviour.
        """
        if self.encoding:
            return line.decode(self.encoding)
        return line

    def send_lines(self, lines):
        """
        Send array of lines to client.

        Join lines using the terminator that is set for this class, encode it
        and send it to the client.
        """
        if not lines:
            return

        data = self.terminator.join(lines)
        self.log_response(data)
        self.send_raw(self.encode(data + self.terminator))

    def send_raw(self, data):
        """Send data to client exactly as is."""
        self.send_lock.acquire(True)
        self.send_buffer += data
        self.send_lock.release()
        self.enable_send()

    def _recv(self, fd, flags):
        # NOTE: This code is _not_ run in the actor's thread, but in the same
        # one as the event loop. If this blocks, rest of gobject code will
        # likely be blocked as well...

        if flags & (gobject.IO_ERR | gobject.IO_HUP):
            actor_ref.stop()
            return False

        try:
            data = self.sock.recv(4096)
        except socket.error as e:
            if e.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                return True
            self.actor_ref.stop()
            return False

        if not data:
            self.actor_ref.stop()
            return False

        self.actor_ref.send_one_way({'received': data})
        return True

    def _send(self, fd, flags):
        # NOTE: This code is _not_ run in the actor's thread...

        # If with can't get the lock, simply try again next time socket is
        # ready for sending.
        if not self.send_lock.acquire(False):
            return True

        try:
            sent = self.sock.send(self.send_buffer)
            self.send_buffer = self.send_buffer[sent:]
            return bool(self.send_buffer)
        except socket.error as e:
            if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                return True
            self.log_error(e)
            self.actor_ref.stop()
            return False
        finally:
            self.send_lock.release()

    def _timeout(self):
        # NOTE: This code is _not_ run in the actor's thread...
        self.log_timeout()
        self.actor_ref.stop()
        return False
