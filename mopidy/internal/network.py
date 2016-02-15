from __future__ import absolute_import, unicode_literals

import errno
import logging
import re
import socket
import sys
import threading

import pykka

from mopidy.internal import encoding
from mopidy.internal.gi import GObject


logger = logging.getLogger(__name__)


class ShouldRetrySocketCall(Exception):

    """Indicate that attempted socket call should be retried"""


def try_ipv6_socket():
    """Determine if system really supports IPv6"""
    if not socket.has_ipv6:
        return False
    try:
        socket.socket(socket.AF_INET6).close()
        return True
    except IOError as error:
        logger.debug(
            'Platform supports IPv6, but socket creation failed, '
            'disabling: %s',
            encoding.locale_decode(error))
    return False


#: Boolean value that indicates if creating an IPv6 socket will succeed.
has_ipv6 = try_ipv6_socket()


def create_socket():
    """Create a TCP socket with or without IPv6 depending on system support"""
    if has_ipv6:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        # Explicitly configure socket to work for both IPv4 and IPv6
        if hasattr(socket, 'IPPROTO_IPV6'):
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        elif sys.platform == 'win32':  # also match 64bit windows.
            # Python 2.7 on windows does not have the IPPROTO_IPV6 constant
            # Use values extracted from Windows Vista/7/8's header
            sock.setsockopt(41, 27, 0)
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock


def format_hostname(hostname):
    """Format hostname for display."""
    if (has_ipv6 and re.match(r'\d+.\d+.\d+.\d+', hostname) is not None):
        hostname = '::ffff:%s' % hostname
    return hostname


class Server(object):

    """Setup listener and register it with GObject's event loop."""

    def __init__(self, host, port, protocol, protocol_kwargs=None,
                 max_connections=5, timeout=30):
        self.protocol = protocol
        self.protocol_kwargs = protocol_kwargs or {}
        self.max_connections = max_connections
        self.timeout = timeout
        self.server_socket = self.create_server_socket(host, port)

        self.register_server_socket(self.server_socket.fileno())

    def create_server_socket(self, host, port):
        sock = create_socket()
        sock.setblocking(False)
        sock.bind((host, port))
        sock.listen(1)
        return sock

    def register_server_socket(self, fileno):
        GObject.io_add_watch(fileno, GObject.IO_IN, self.handle_connection)

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
        return len(pykka.ActorRegistry.get_by_class(self.protocol))

    def reject_connection(self, sock, addr):
        # FIXME provide more context in logging?
        logger.warning('Rejected connection from [%s]:%s', addr[0], addr[1])
        try:
            sock.close()
        except socket.error:
            pass

    def init_connection(self, sock, addr):
        Connection(
            self.protocol, self.protocol_kwargs, sock, addr, self.timeout)


class Connection(object):
    # NOTE: the callback code is _not_ run in the actor's thread, but in the
    # same one as the event loop. If code in the callbacks blocks, the rest of
    # GObject code will likely be blocked as well...
    #
    # Also note that source_remove() return values are ignored on purpose, a
    # false return value would only tell us that what we thought was registered
    # is already gone, there is really nothing more we can do.

    def __init__(self, protocol, protocol_kwargs, sock, addr, timeout):
        sock.setblocking(False)

        self.host, self.port = addr[:2]  # IPv6 has larger addr

        self.sock = sock
        self.protocol = protocol
        self.protocol_kwargs = protocol_kwargs
        self.timeout = timeout

        self.send_lock = threading.Lock()
        self.send_buffer = b''

        self.stopping = False

        self.recv_id = None
        self.send_id = None
        self.timeout_id = None

        self.actor_ref = self.protocol.start(self, **self.protocol_kwargs)

        self.enable_recv()
        self.enable_timeout()

    def stop(self, reason, level=logging.DEBUG):
        if self.stopping:
            logger.log(level, 'Already stopping: %s' % reason)
            return
        else:
            self.stopping = True

        logger.log(level, reason)

        try:
            self.actor_ref.stop(block=False)
        except pykka.ActorDeadError:
            pass

        self.disable_timeout()
        self.disable_recv()
        self.disable_send()

        try:
            self.sock.close()
        except socket.error:
            pass

    def queue_send(self, data):
        """Try to send data to client exactly as is and queue rest."""
        self.send_lock.acquire(True)
        self.send_buffer = self.send(self.send_buffer + data)
        self.send_lock.release()
        if self.send_buffer:
            self.enable_send()

    def send(self, data):
        """Send data to client, return any unsent data."""
        try:
            sent = self.sock.send(data)
            return data[sent:]
        except socket.error as e:
            if e.errno in (errno.EWOULDBLOCK, errno.EINTR):
                return data
            self.stop(
                'Unexpected client error: %s' % encoding.locale_decode(e))
            return b''

    def enable_timeout(self):
        """Reactivate timeout mechanism."""
        if self.timeout <= 0:
            return

        self.disable_timeout()
        self.timeout_id = GObject.timeout_add_seconds(
            self.timeout, self.timeout_callback)

    def disable_timeout(self):
        """Deactivate timeout mechanism."""
        if self.timeout_id is None:
            return
        GObject.source_remove(self.timeout_id)
        self.timeout_id = None

    def enable_recv(self):
        if self.recv_id is not None:
            return

        try:
            self.recv_id = GObject.io_add_watch(
                self.sock.fileno(),
                GObject.IO_IN | GObject.IO_ERR | GObject.IO_HUP,
                self.recv_callback)
        except socket.error as e:
            self.stop('Problem with connection: %s' % e)

    def disable_recv(self):
        if self.recv_id is None:
            return
        GObject.source_remove(self.recv_id)
        self.recv_id = None

    def enable_send(self):
        if self.send_id is not None:
            return

        try:
            self.send_id = GObject.io_add_watch(
                self.sock.fileno(),
                GObject.IO_OUT | GObject.IO_ERR | GObject.IO_HUP,
                self.send_callback)
        except socket.error as e:
            self.stop('Problem with connection: %s' % e)

    def disable_send(self):
        if self.send_id is None:
            return

        GObject.source_remove(self.send_id)
        self.send_id = None

    def recv_callback(self, fd, flags):
        if flags & (GObject.IO_ERR | GObject.IO_HUP):
            self.stop('Bad client flags: %s' % flags)
            return True

        try:
            data = self.sock.recv(4096)
        except socket.error as e:
            if e.errno not in (errno.EWOULDBLOCK, errno.EINTR):
                self.stop('Unexpected client error: %s' % e)
            return True

        if not data:
            self.disable_recv()
            self.actor_ref.tell({'close': True})
            return True

        try:
            self.actor_ref.tell({'received': data})
        except pykka.ActorDeadError:
            self.stop('Actor is dead.')

        return True

    def send_callback(self, fd, flags):
        if flags & (GObject.IO_ERR | GObject.IO_HUP):
            self.stop('Bad client flags: %s' % flags)
            return True

        # If with can't get the lock, simply try again next time socket is
        # ready for sending.
        if not self.send_lock.acquire(False):
            return True

        try:
            self.send_buffer = self.send(self.send_buffer)
            if not self.send_buffer:
                self.disable_send()
        finally:
            self.send_lock.release()

        return True

    def timeout_callback(self):
        self.stop('Client inactive for %ds; closing connection' % self.timeout)
        return False


class LineProtocol(pykka.ThreadingActor):

    """
    Base class for handling line based protocols.

    Takes care of receiving new data from server's client code, decoding and
    then splitting data along line boundaries.
    """

    #: Line terminator to use for outputed lines.
    terminator = '\n'

    #: Regex to use for spliting lines, will be set compiled version of its
    #: own value, or to ``terminator``s value if it is not set itself.
    delimiter = None

    #: What encoding to expect incomming data to be in, can be :class:`None`.
    encoding = 'utf-8'

    def __init__(self, connection):
        super(LineProtocol, self).__init__()
        self.connection = connection
        self.prevent_timeout = False
        self.recv_buffer = b''

        if self.delimiter:
            self.delimiter = re.compile(self.delimiter)
        else:
            self.delimiter = re.compile(self.terminator)

    @property
    def host(self):
        return self.connection.host

    @property
    def port(self):
        return self.connection.port

    def on_line_received(self, line):
        """
        Called whenever a new line is found.

        Should be implemented by subclasses.
        """
        raise NotImplementedError

    def on_receive(self, message):
        """Handle messages with new data from server."""
        if 'close' in message:
            self.connection.stop('Client most likely disconnected.')
            return

        if 'received' not in message:
            return

        self.connection.disable_timeout()
        self.recv_buffer += message['received']

        for line in self.parse_lines():
            line = self.decode(line)
            if line is not None:
                self.on_line_received(line)

        if not self.prevent_timeout:
            self.connection.enable_timeout()

    def on_stop(self):
        """Ensure that cleanup when actor stops."""
        self.connection.stop('Actor is shutting down.')

    def parse_lines(self):
        """Consume new data and yield any lines found."""
        while re.search(self.terminator, self.recv_buffer):
            line, self.recv_buffer = self.delimiter.split(
                self.recv_buffer, 1)
            yield line

    def encode(self, line):
        """
        Handle encoding of line.

        Can be overridden by subclasses to change encoding behaviour.
        """
        try:
            return line.encode(self.encoding)
        except UnicodeError:
            logger.warning(
                'Stopping actor due to encode problem, data '
                'supplied by client was not valid %s',
                self.encoding)
            self.stop()

    def decode(self, line):
        """
        Handle decoding of line.

        Can be overridden by subclasses to change decoding behaviour.
        """
        try:
            return line.decode(self.encoding)
        except UnicodeError:
            logger.warning(
                'Stopping actor due to decode problem, data '
                'supplied by client was not valid %s',
                self.encoding)
            self.stop()

    def join_lines(self, lines):
        if not lines:
            return ''
        return self.terminator.join(lines) + self.terminator

    def send_lines(self, lines):
        """
        Send array of lines to client via connection.

        Join lines using the terminator that is set for this class, encode it
        and send it to the client.
        """
        if not lines:
            return

        data = self.join_lines(lines)
        self.connection.queue_send(self.encode(data))
