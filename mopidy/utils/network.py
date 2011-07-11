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

class ShouldRetrySocketCall(Exception):
    """Indicate that attempted socket call should be retried"""

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

    def __init__(self, host, port, protocol, max_connections=5, timeout=30):
        self.protocol = protocol
        self.max_connections = max_connections
        self.timeout = timeout
        self.server_socket = self.create_server_socket(host, port)

        self.register_server_socket(self.server_socket.fileno())

        logger.debug(u'Listening on [%s]:%s using %s as protocol handler',
            host, port, self.protocol)

    def create_server_socket(self, host, port):
        sock = create_socket()
        sock.setblocking(False)
        sock.bind((host, port))
        sock.listen(1)
        return sock

    def register_server_socket(self, fileno):
        gobject.io_add_watch(fileno, gobject.IO_IN, self.handle_connection)

    def handle_connection(self, fd, flags):
        try:
            sock, addr = self.accept_connection()
        except ShouldRetrySocketCall:
            return True

        if self.maximum_connections_exceeded():
            self.reject_connection(sock, addr)
        else:
            self.init_connection(sock, addr)
        return True

    def accept_connection(self):
        try:
            return self.server_socket.accept()
        except socket.error as e:
            if e.errno in (errno.EAGAIN, errno.EINTR):
                raise ShouldRetrySocketCall
            raise

    def maximum_connections_exceeded(self):
        return (self.max_connections is not None and
                self.number_of_connections() >= self.max_connections)

    def number_of_connections(self):
        return len(ActorRegistry.get_by_class(self.protocol))

    def reject_connection(self, sock, addr):
        logger.warning(u'Rejected connection from [%s]:%s', addr[0], addr[1])
        try:
            sock.close()
        except socket.error:
            pass

    def init_connection(self, sock, addr):
        Connection(self.protocol, sock, addr, self.timeout)

class Connection(object):
    def __init__(self, protocol, sock, addr, timeout):
        sock.setblocking(False)

        self.host, self.port = addr[:2] # IPv6 has larger addr

        self._sock = sock
        self._protocol = protocol
        self._timeout_time = timeout

        self._send_lock = threading.Lock()
        self._send_buffer = ''

        self._recv_id = None
        self._send_id = None
        self._timeout_id = None

        self._actor_ref = self._protocol.start(self)

        self._enable_recv()
        self.enable_timeout()

    def stop(self):
        self._actor_ref.stop()
        self.disable_timeout()
        self._disable_recv()
        self._disable_send()
        try:
            self._sock.close()
        except socket.error:
            pass
        return False

    def send(self, data):
        """Send data to client exactly as is."""
        self._send_lock.acquire(True)
        self._send_buffer += data
        self._send_lock.release()
        self._enable_send()

    def enable_timeout(self):
        """Reactivate timeout mechanism."""
        self.disable_timeout()
        if self._timeout_time > 0:
            self._timeout_id = gobject.timeout_add_seconds(
                self._timeout_time, self._timeout)

    def disable_timeout(self):
        """Deactivate timeout mechanism."""
        if self._timeout_id is not None:
            gobject.source_remove(self._timeout_id)
            self._timeout_id = None

    def _enable_recv(self):
        if self._recv_id is None:
            self._recv_id = gobject.io_add_watch(self._sock.fileno(),
                gobject.IO_IN | gobject.IO_ERR | gobject.IO_HUP, self._recv)

    def _disable_recv(self):
        if self._recv_id is not None:
            gobject.source_remove(self._recv_id)
            self._recv_id = None

    def _enable_send(self):
        if self._send_id is None:
            self._send_id = gobject.io_add_watch(self._sock.fileno(),
                gobject.IO_OUT | gobject.IO_ERR | gobject.IO_HUP, self._send)

    def _disable_send(self):
        if self._send_id:
            gobject.source_remove(self._send_id)
            self._send_id = None

    def _recv(self, fd, flags):
        # NOTE: This code is _not_ run in the actor's thread, but in the same
        # one as the event loop. If this blocks, rest of gobject code will
        # likely be blocked as well...

        if flags & (gobject.IO_ERR | gobject.IO_HUP):
            return self.stop()

        try:
            data = self._sock.recv(4096)
        except socket.error as e:
            if e.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                return True
            return self.stop()

        if not data:
            return self.stop()

        self._actor_ref.send_one_way({'received': data})
        return True

    def _send(self, fd, flags):
        # NOTE: This code is _not_ run in the actor's thread...

        # If with can't get the lock, simply try again next time socket is
        # ready for sending.
        if not self._send_lock.acquire(False):
            return True

        try:
            sent = self._sock.send(self._send_buffer)
            self._send_buffer = self._send_buffer[sent:]
            if not self._send_buffer:
                self._disable_send()
        except socket.error as e:
            if e.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                #self.log_error(e) # FIXME log error
                return self.stop()
        finally:
            self._send_lock.release()

        return True

    def _timeout(self):
        # NOTE: This code is _not_ run in the actor's thread...
        #self.log_timeout() # FIXME log this
        return self.stop()


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

    def __init__(self, connection):
        self.connection = connection

        self.recv_buffer = ''
        self.terminator_re = re.compile(self.terminator)

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

        self.connection.disable_timeout()
        self.log_raw_data(message['received'])

        for line in self.parse_lines(message['received']):
            line = self.decode(line)
            self.log_request(line)
            self.on_line_received(line)

        self.connection.enable_timeout()

    def on_stop(self):
        """Ensure that cleanup when actor stops."""
        self.connection.stop()

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
        logger.debug(u'Got %s from event loop in %s', repr(data),
            self.actor_urn)

    def log_request(self, request):
        """
        Log request for debug purposes.

        Can be overridden by subclasses to change logging behaviour.
        """
        logger.debug(u'Request from %s to %s: %s', self.connection, self.actor_urn,
            indent(request))

    def log_response(self, response):
        """
        Log response for debug purposes.

        Can be overridden by subclasses to change logging behaviour.
        """
        logger.debug(u'Response to %s from %s: %s', self.connection,
            self.actor_urn, indent(response))

    def log_error(self, error):
        """
        Log error for debug purposes.

        Can be overridden by subclasses to change logging behaviour.
        """
        logger.warning(u'Problem with connection to %s in %s: %s',
            self.connection, self.actor_urn, error)

    def log_timeout(self):
        """
        Log timeout for debug purposes.

        Can be overridden by subclasses to change logging behaviour.
        """
        logger.debug(u'Closing connection to %s in %s due to timeout.',
            self.connection, self.actor_urn)

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
        Send array of lines to client via connection.

        Join lines using the terminator that is set for this class, encode it
        and send it to the client.
        """
        if not lines:
            return

        data = self.terminator.join(lines)
        self.log_response(data)
        self.connection.send(self.encode(data + self.terminator))
