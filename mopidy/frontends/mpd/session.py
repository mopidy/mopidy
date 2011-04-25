import asynchat
import logging

from mopidy import settings
from mopidy.frontends.mpd.dispatcher import MpdDispatcher
from mopidy.frontends.mpd.protocol import ENCODING, LINE_TERMINATOR, VERSION
from mopidy.utils.log import indent

logger = logging.getLogger('mopidy.frontends.mpd.session')

class MpdSession(asynchat.async_chat):
    """
    The MPD client session. Keeps track of a single client session. Any
    requests from the client is passed on to the MPD request dispatcher.
    """

    def __init__(self, server, client_socket, client_socket_address):
        asynchat.async_chat.__init__(self, sock=client_socket)
        self.server = server
        self.client_address = client_socket_address[0]
        self.client_port = client_socket_address[1]
        self.input_buffer = []
        self.authenticated = False
        self.set_terminator(LINE_TERMINATOR.encode(ENCODING))
        self.dispatcher = MpdDispatcher()

    def start(self):
        """Start a new client session."""
        self.send_response(u'OK MPD %s' % VERSION)

    def collect_incoming_data(self, data):
        """Collect incoming data into buffer until a terminator is found."""
        self.input_buffer.append(data)

    def found_terminator(self):
        """Handle request when a terminator is found."""
        data = ''.join(self.input_buffer).strip()
        self.input_buffer = []
        try:
            request = data.decode(ENCODING)
            logger.debug(u'Input from [%s]:%s: %s', self.client_address,
                self.client_port, indent(request))
            self.handle_request(request)
        except UnicodeDecodeError as e:
            logger.warning(u'Received invalid data: %s', e)

    def handle_request(self, request):
        """Handle request by sending it to the MPD frontend."""
        if not self.authenticated:
            (self.authenticated, response) = self.check_password(request)
            if response is not None:
                self.send_response(response)
                return
        response = self.dispatcher.handle_request(request)
        if response is not None:
            self.handle_response(response)

    def handle_response(self, response):
        """Handle response from the MPD frontend."""
        self.send_response(LINE_TERMINATOR.join(response))

    def send_response(self, output):
        """Send a response to the client."""
        logger.debug(u'Output to [%s]:%s: %s', self.client_address,
            self.client_port, indent(output))
        output = u'%s%s' % (output, LINE_TERMINATOR)
        data = output.encode(ENCODING)
        self.push(data)

    def check_password(self, request):
        """
        Takes any request and tries to authenticate the client using it.

        :rtype: a two-tuple containing (is_authenticated, response_message). If
            the response_message is :class:`None`, normal processing should
            continue, even though the client may not be authenticated.
        """
        if settings.MPD_SERVER_PASSWORD is None:
            return (True, None)
        command = request.split(' ')[0]
        if command == 'password':
            if request == 'password "%s"' % settings.MPD_SERVER_PASSWORD:
                return (True, u'OK')
            else:
                return (False, u'ACK [3@0] {password} incorrect password')
        if command in ('close', 'commands', 'notcommands', 'ping'):
            return (False, None)
        else:
            return (False,
                u'ACK [4@0] {%(c)s} you don\'t have permission for "%(c)s"' %
                {'c': command})
