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

class Listener(object):
    """Setup listener and register it with gobject loop."""

    def __init__(self, host, port, protcol):
        self.protcol = protcol
        self.listener = create_socket()
        self.listener.setblocking(False)
        self.listener.bind((host, port))
        self.listener.listen(1)

        gobject.io_add_watch(
            self.listener.fileno(), gobject.IO_IN, self.handle_accept)
        logger.debug('Listening on [%s]:%s using %s as protcol handler',
            host, port, self.protcol.__name__)

    def handle_accept(self, fd, flags):
        sock, addr = self.listener.accept()
        sock.setblocking(False)

        actor_ref = self.protcol.start(sock, addr)
        gobject.io_add_watch(sock.fileno(), gobject.IO_IN | gobject.IO_ERR |
            gobject.IO_HUP, self.handle_client, sock, actor_ref)

        return True

    def handle_client(self, fd, flags, sock, actor_ref):
        if flags & (gobject.IO_ERR | gobject.IO_HUP):
            data = ''
        else:
            data = sock.recv(1024)

        if not data:
            actor_ref.stop()
            return False

        actor_ref.send_one_way({'recvieved': data})
        return True


class LineProtocol(ThreadingActor):
    terminator = '\n'
    encoding = 'utf-8'

    def __init__(self, sock, addr):
        self.sock = sock
        self.host, self.port = addr
        self.recv_buffer = ''

    def on_line_recieved(self, line):
        raise NotImplemented

    def on_receive(self, message):
        if 'recvieved' not in message:
            return

        for line in self.parse_lines(message['recvieved']):
            line = self.encode(line)
            self.log_request(line)
            self.on_line_recieved(line)

    def on_stop(self):
        try:
            self.sock.close()
        except socket.error as e:
            pass

    def parse_lines(self, new_data=None):
        if new_data:
            self.recv_buffer += new_data
        while self.terminator in self.recv_buffer:
            line, self.recv_buffer = self.recv_buffer.split(self.terminator, 1)
            yield line

    def log_request(self, request):
        logger.debug(u'Request from [%s]:%s: %s',
            self.host, self.port, indent(request))

    def log_response(self, response):
        logger.debug(u'Response to [%s]:%s: %s',
            self.host, self.port, indent(response))

    def encode(self, line):
        if self.encoding:
            return line.encode(self.encoding)
        return line

    def decode(self, line):
        if self.encoding:
            return line.decode(self.encoding)
        return line

    def send_lines(self, lines):
        if not lines:
            return

        data = self.terminator.join(lines)
        self.log_response(data)
        self.send_raw(self.encode(data + self.terminator))

    def send_raw(self, data):
        try:
            sent = self.sock.send(data)
            assert len(data) == sent, 'All data was not sent' # FIXME
        except socket.error as e: # FIXME
            logger.debug('send() failed with: %s', e)
            self.stop()
