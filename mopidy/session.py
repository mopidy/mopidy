import asynchat
import logging

from mopidy import get_mpd_version, settings
from mopidy.handler import MpdHandler

logger = logging.getLogger(u'session')

class MpdSession(asynchat.async_chat):
    def __init__(self, client_socket, client_address, handler=MpdHandler):
        asynchat.async_chat.__init__(self, sock=client_socket)
        self.client_address = client_address
        self.input_buffer = []
        self.set_terminator(settings.MPD_LINE_TERMINATOR)
        self.handler = handler(session=self)
        self.send_response(u'OK MPD %s' % get_mpd_version())

    def close_when_done(self):
        logger.info(u'Closing connection with [%s]:%s', *self.client_address)
        asynchat.async_chat.close_when_done(self)

    def collect_incoming_data(self, data):
        self.input_buffer.append(data)

    def found_terminator(self):
        data = ''.join(self.input_buffer).strip()
        self.input_buffer = []
        input = data.decode(settings.MPD_LINE_ENCODING)
        logger.debug(u'Input: %s', input)
        self.handle_request(input)

    def handle_request(self, input):
        response = self.handler.handle_request(input)
        if isinstance(response, list):
            for line in response:
                self.send_response(line)
        elif isinstance(response, dict):
            for key, value in response.items():
                self.send_response(u'%s: %s' % (key, value))
        elif response is not None:
            self.send_response(response)
        self.send_response(u'OK')

    def send_response(self, output):
        logger.debug(u'Output: %s', output)
        output = u'%s%s' % (output, settings.MPD_LINE_TERMINATOR)
        data = output.encode(settings.MPD_LINE_ENCODING)
        self.push(data)

