import asynchat
import logging

from mopidy import get_version, settings

logger = logging.getLogger('session')

class MpdSession(asynchat.async_chat):
    def __init__(self, client_socket, client_address):
        asynchat.async_chat.__init__(self, sock=client_socket)
        self.input_buffer = []
        self.set_terminator(settings.LINE_TERMINATOR)
        self.respond('OK MPD (mopidy %s)' % get_version())

    def collect_incoming_data(self, data):
        self.input_buffer.append(data)

    def found_terminator(self):
        logger.debug('Input: %s', ''.join(self.input_buffer))
        self.input_buffer = []

    def respond(self, data):
        self.push('%s%s' % (data, settings.LINE_TERMINATOR))
