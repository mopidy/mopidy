import gobject
import logging
import sys

from pykka.actor import ThreadingActor

from mopidy.frontends.base import BaseFrontend
from mopidy import settings
from mopidy.utils import network
from mopidy.frontends.mpd.dispatcher import MpdDispatcher
from mopidy.frontends.mpd.protocol import ENCODING, VERSION, LINE_TERMINATOR
from mopidy.utils.log import indent

logger = logging.getLogger('mopidy.frontends.mpd')

# FIXME no real need for frontend to be threading actor
class MpdFrontend(ThreadingActor, BaseFrontend):
    """
    The MPD frontend.

    **Dependencies:**

    - None

    **Settings:**

    - :attr:`mopidy.settings.MPD_SERVER_HOSTNAME`
    - :attr:`mopidy.settings.MPD_SERVER_PORT`
    - :attr:`mopidy.settings.MPD_SERVER_PASSWORD`
    """

    def __init__(self):
        hostname = network.format_hostname(settings.MPD_SERVER_HOSTNAME)
        port = settings.MPD_SERVER_PORT

        try:
            network.Listener(hostname, port, session=MpdSession)
        except IOError, e:
            logger.error(u'MPD server startup failed: %s', e)
            sys.exit(1)

        logger.info(u'MPD server running at [%s]:%s', hostname, port)


class MpdSession(ThreadingActor):
    """
    The MPD client session. Keeps track of a single client session. Any
    requests from the client is passed on to the MPD request dispatcher.
    """

    def __init__(self, sock, addr):
        self.sock = sock # Prevent premature GC of socket closing it
        self.addr = addr
        self.channel = gobject.IOChannel(sock.fileno())
        self.dispatcher = MpdDispatcher()

    def on_start(self):
        try:
            self.send_response([u'OK MPD %s' % VERSION])
            self.request_loop()
        except gobject.GError:
            self.stop()

    def close(self):
        self.channel.close()

    def request_loop(self):
        while True:
            data = self.channel.readline()
            if not data:
                return self.close()
            request = data.rstrip(LINE_TERMINATOR).decode(ENCODING)
            logger.debug(u'Request from [%s]:%s: %s', self.addr[0],
                self.addr[1], indent(request))
            response = self.dispatcher.handle_request(request)
            self.send_response(response)

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
            self.channel.write(data)
            self.channel.flush()
