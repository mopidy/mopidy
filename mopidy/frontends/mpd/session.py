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
        self.dispatcher = MpdDispatcher(session=self)

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
        """Handle request using the MPD command handlers."""
        response = self.dispatcher.handle_request(request)
        if response is not None:
            self.handle_response(response)

    def handle_response(self, response):
        """Handle response from the MPD command handlers."""
        self.send_response(LINE_TERMINATOR.join(response))

    def send_response(self, output):
        """Send a response to the client."""
        logger.debug(u'Output to [%s]:%s: %s', self.client_address,
            self.client_port, indent(output))
        output = u'%s%s' % (output, LINE_TERMINATOR)
        data = output.encode(ENCODING)
        self.push(data)
