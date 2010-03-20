import asynchat
import asyncore
import logging
import multiprocessing
import socket
import sys
import time

from mopidy import get_mpd_protocol_version, pickle_connection, settings
from mopidy.mpd import MpdAckError

logger = logging.getLogger(u'mpd.server')

#: All data between the client and the server is encoded in UTF-8.
ENCODING = u'utf-8'

LINE_TERMINATOR = u'\n'

class MpdServer(asyncore.dispatcher):
    def __init__(self, core_queue=None):
        asyncore.dispatcher.__init__(self)
        self.core_queue = core_queue
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((settings.SERVER_HOSTNAME, settings.SERVER_PORT))
        self.listen(1)
        self.started_at = int(time.time())
        logger.info(u'Please connect to %s port %s using an MPD client.',
            settings.SERVER_HOSTNAME, settings.SERVER_PORT)

    def handle_accept(self):
        (client_socket, client_address) = self.accept()
        logger.info(u'Connection from: [%s]:%s', *client_address)
        MpdSession(self, client_socket, client_address, self.core_queue)

    def handle_close(self):
        self.close()

    def do_kill(self):
        logger.info(u'Received "kill". Shutting down.')
        self.handle_close()
        sys.exit(0)

    @property
    def uptime(self):
        return int(time.time()) - self.started_at


class MpdSession(asynchat.async_chat):
    def __init__(self, server, client_socket, client_address, core_queue):
        asynchat.async_chat.__init__(self, sock=client_socket)
        self.server = server
        self.client_address = client_address
        self.core_queue = core_queue
        self.input_buffer = []
        self.set_terminator(LINE_TERMINATOR.encode(ENCODING))
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
        input = data.decode(ENCODING)
        logger.debug(u'Input: %s', indent(input))
        self.handle_request(input)

    def handle_request(self, input):
        try:
            my_end, other_end = multiprocessing.Pipe()
            self.core_queue.put({
                'command': 'mpd_request',
                'request': input,
                'reply_to': pickle_connection(other_end),
            })
            my_end.poll(None)
            response = my_end.recv()
            if response is not None:
                self.handle_response(response)
        except MpdAckError, e:
            logger.warning(e)
            return self.send_response(u'ACK %s' % e)

    def handle_response(self, response):
        self.send_response(LINE_TERMINATOR.join(response))

    def send_response(self, output):
        logger.debug(u'Output: %s', indent(output))
        output = u'%s%s' % (output, LINE_TERMINATOR)
        data = output.encode(ENCODING)
        self.push(data)

    def stats_uptime(self):
        return self.server.uptime


def indent(string, places=4, linebreak=LINE_TERMINATOR):
    lines = string.split(linebreak)
    if len(lines) == 1:
        return string
    result = u''
    for line in lines:
        result += linebreak + ' ' * places + line
    return result
