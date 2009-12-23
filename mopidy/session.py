import asynchat
import logging

from mopidy import get_version, settings

logger = logging.getLogger(u'session')

class MpdSession(asynchat.async_chat):
    def __init__(self, client_socket, client_address):
        asynchat.async_chat.__init__(self, sock=client_socket)
        self.input_buffer = []
        self.set_terminator(settings.MPD_LINE_TERMINATOR)
        self.send_response(u'OK MPD (mopidy %s)' % get_version())

    def collect_incoming_data(self, data):
        self.input_buffer.append(data)

    def found_terminator(self):
        data = ''.join(self.input_buffer)
        self.input_buffer = []
        input = data.decode(settings.MPD_LINE_ENCODING)
        logger.debug(u'Input: %s', input)
        self.handle_request(input)

    def handle_request(self, input):
        pass # TODO

    def send_response(self, output):
        logger.debug(u'Output: %s', output)
        output = u'%s%s' % (output, settings.MPD_LINE_TERMINATOR)
        data = output.encode(settings.MPD_LINE_ENCODING)
        self.push(data)

