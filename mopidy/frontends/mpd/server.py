import logging
import sys

import gobject

from mopidy import settings
from mopidy.utils import network
from mopidy.frontends.mpd.dispatcher import MpdDispatcher
from mopidy.frontends.mpd.protocol import ENCODING, LINE_TERMINATOR, VERSION
from mopidy.utils.log import indent

logger = logging.getLogger('mopidy.frontends.mpd.server')

class MpdServer(object):
    """
    The MPD server. Creates a :class:`mopidy.frontends.mpd.session.MpdSession`
    for each client connection.
    """

    def start(self):
        """Start MPD server."""
        try:
            hostname = network.format_hostname(settings.MPD_SERVER_HOSTNAME)
            port = settings.MPD_SERVER_PORT
            logger.debug(u'MPD server is binding to [%s]:%s', hostname, port)
            network.Listener((hostname, port), handler=MpdHandler)
            logger.info(u'MPD server running at [%s]:%s', hostname, port)
        except IOError, e:
            logger.error(u'MPD server startup failed: %s' %
                str(e).decode('utf-8'))
            sys.exit(1)


class MpdHandler(network.BaseHandler):
    """
    The MPD client session. Keeps track of a single client session. Any
    requests from the client is passed on to the MPD request dispatcher.
    """

    terminator = LINE_TERMINATOR

    def __init__(self, (sock, addr)):
        super(MpdHandler, self).__init__((sock, addr))
        self.dispatcher = MpdDispatcher(session=self)
        self.send_response([u'OK MPD %s' % VERSION])

    def recv(self, line):
        """Handle the request using the MPD command handlers."""
        request = line.decode(ENCODING)
        logger.debug(u'Request from [%s]:%s: %s', self.addr[0],
            self.addr[1], indent(request))
        self.send_response(self.dispatcher.handle_request(request))

    def send_response(self, response):
        """
        Format a response from the MPD command handlers and send it to the
        client.
        """
        if response:
            response = LINE_TERMINATOR.join(response)
            logger.debug(u'Response to [%s]:%s: %s', self.addr[0],
                self.addr[1], indent(response))
            response = u'%s%s' % (response, LINE_TERMINATOR)
            data = response.encode(ENCODING)
            self.send(data)
