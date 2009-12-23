import asynchat
import logging

logger = logging.getLogger('session')

class MpdSession(asynchat.async_chat):
    def __init__(self, client_socket, client_address):
        asynchat.async_chat.__init__(self, sock=client_socket)
        self.input_buffer = []
        self.set_terminator('\n')

    def collect_incoming_data(self, data):
        self.input_buffer.append(data)

    def found_terminator(self):
        logger.debug('Input: %s', ''.join(self.input_buffer))
        self.input_buffer = []
