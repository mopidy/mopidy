import logging
import re
import socket
import gobject

from pykka.actor import ThreadingActor

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
    """Setup listener and register it with gobject loop."""

    def __init__(self, host, port, protocol):
        self.protocol = protocol
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

        sock.setblocking(False)

        actor_ref = self.protocol.start(sock, addr)
        gobject.io_add_watch(sock.fileno(), gobject.IO_IN | gobject.IO_ERR |
            gobject.IO_HUP, self.handle_client, sock, actor_ref)

        return True

    def handle_client(self, fd, flags, sock, actor_ref):
        """
        Read client data when possible.

        Returns false when reading failed in order to deregister with the event
        loop.
        """
        if flags & (gobject.IO_ERR | gobject.IO_HUP):
            data = ''
        else:
            data = sock.recv(1024) # FIXME there are cases where this might fail.

        if not data:
            actor_ref.stop()
            return False

        actor_ref.send_one_way({'received': data})
        return True


class LineProtocol(ThreadingActor):
    """
    Base class for handling line based protocols.

    Takes care of receiving new data from listener's client code, decoding and
    then splitting data along line boundaries.

    Attributes ``terminator``and ``encoding`` can be set in case subclasses
    want to split by another terminator or use another encoding.
    """

    terminator = '\n'
    encoding = 'utf-8'

    def __init__(self, sock, addr):
        self.sock = sock
        self.host, self.port = addr[:2]
        self.recv_buffer = ''

    def on_line_received(self, line):
        """
        Called whenever a new line is found.

        Should be implemented by subclasses.
        """
        raise NotImplemented

    def on_receive(self, message):
        """Handle messages with new data from listener."""
        if 'received' not in message:
            return

        self.log_raw_data(message['received'])

        for line in self.parse_lines(message['received']):
            line = self.decode(line)
            self.log_request(line)
            self.on_line_received(line)

    def on_stop(self):
        """Ensure that socket is closed when actor stops."""
        try:
            self.sock.close()
        except socket.error:
            pass

    def parse_lines(self, new_data=None):
        """Consume new data and yield any lines found."""
        if new_data:
            self.recv_buffer += new_data
        while self.terminator in self.recv_buffer:
            line, self.recv_buffer = self.recv_buffer.split(self.terminator, 1)
            yield line

    def log_raw_data(self, data):
        """
        Log raw data from event loopfor debug purposes.

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
        try:
            sent = self.sock.send(data)
            # FIXME we are assuming that sock send will not fail as the OS send
            # buffer is big enough compared to our need. This can of course
            # fail and will be caught and handled fairly poorly with the
            # following assert.
            #
            # Safer, and more complex way of handling this would be to ensure
            # that data can be send by putting a data sender in the event loop
            # and appending to its buffer. Once the buffer is empty the sender
            # must be removed from the loop. This option is doable, but adds
            # extra complexity.
            #
            # The other simpler option would be to try and recall raw_send with
            # remaining data. Probably with a decrementing retry counter to
            # prevent an inf. loop.
            assert len(data) == sent, u'All data was not sent'
        except socket.error as e:
            # FIXME should this be handled in a better manner, for instance
            # retry? For instance would block errors and interrupted system call
            # errors would warrant a retry.
            logger.debug(u'send() failed with: %s', e)
            self.stop()
