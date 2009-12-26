import asynchat
import logging

from mopidy import get_mpd_protocol_version, settings
from mopidy.exceptions import MpdAckError
from mopidy.handler import MpdHandler

logger = logging.getLogger(u'session')

class MpdSession(asynchat.async_chat):
    def __init__(self, server, client_socket, client_address, backend,
            handler_class=MpdHandler):
        asynchat.async_chat.__init__(self, sock=client_socket)
        self.server = server
        self.client_address = client_address
        self.input_buffer = []
        self.set_terminator(settings.MPD_LINE_TERMINATOR.encode(
            settings.MPD_LINE_ENCODING))
        self.handler = handler_class(session=self, backend=backend)
        self.send_response(u'OK MPD %s' % get_mpd_protocol_version())

    def do_close(self):
        logger.info(u'Closing connection with [%s]:%s', *self.client_address)
        self.close_when_done()

    def do_kill(self):
        self.server.do_kill()

    def collect_incoming_data(self, data):
        self.input_buffer.append(data)

    def found_terminator(self):
        data = ''.join(self.input_buffer).strip()
        self.input_buffer = []
        input = data.decode(settings.MPD_LINE_ENCODING)
        logger.debug(u'Input: %s', input)
        self.handle_request(input)

    def handle_request(self, input):
        try:
            response = self.handler.handle_request(input)
            self.handle_response(response)
        except MpdAckError, e:
            logger.warning(e)
            return self.send_response(u'ACK %s' % e)

    def handle_response(self, response):
        for line in response:
            self.send_response(line)

    def send_response(self, output):
        logger.debug(u'Output: %s', output)
        output = u'%s%s' % (output, settings.MPD_LINE_TERMINATOR)
        data = output.encode(settings.MPD_LINE_ENCODING)
        self.push(data)
