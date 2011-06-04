import asynchat
import logging

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
        self.send_response([u'OK MPD %s' % VERSION])

    def collect_incoming_data(self, data):
        """Called by asynchat when new data arrives."""
        self.input_buffer.append(data)

    def found_terminator(self):
        """Called by asynchat when a terminator is found in incoming data."""
        data = ''.join(self.input_buffer).strip()
        self.input_buffer = []
        try:
            self.send_response(self.handle_request(data))
        except UnicodeDecodeError as e:
            logger.warning(u'Received invalid data: %s', e)

    def handle_request(self, request):
        """Handle the request using the MPD command handlers."""
        request = request.decode(ENCODING)
        logger.debug(u'Request from [%s]:%s: %s', self.client_address,
            self.client_port, indent(request))
        return self.dispatcher.handle_request(request)

    def send_response(self, response):
        """
        Format a response from the MPD command handlers and send it to the
        client.
        """
        if response is not None:
            response = LINE_TERMINATOR.join(response)
            logger.debug(u'Response to [%s]:%s: %s', self.client_address,
                self.client_port, indent(response))
            response = u'%s%s' % (response, LINE_TERMINATOR)
            data = response.encode(ENCODING)
            self.push(data)
