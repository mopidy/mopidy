import logging
import sys

from pykka.actor import ThreadingActor

from mopidy import settings
from mopidy.utils import network
from mopidy.utils.process import stop_actors_by_class
from mopidy.frontends.mpd.dispatcher import MpdDispatcher
from mopidy.frontends.mpd.protocol import ENCODING, VERSION, LINE_TERMINATOR

logger = logging.getLogger('mopidy.frontends.mpd')

class MpdFrontend(ThreadingActor):
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
            network.Listener(hostname, port, MpdSession)
        except IOError, e:
            logger.error(u'MPD server startup failed: %s', e)
            sys.exit(1)

        logger.info(u'MPD server running at [%s]:%s', hostname, port)

    def on_receive(self, message):
        pass # Ignore state info that is sent to frontend.

    def on_stop(self):
        stop_actors_by_class(MpdSession)


class MpdSession(network.LineProtocol):
    """
    The MPD client session. Keeps track of a single client session. Any
    requests from the client is passed on to the MPD request dispatcher.
    """

    terminator = LINE_TERMINATOR
    encoding = ENCODING

    def __init__(self, sock, addr):
        super(MpdSession, self).__init__(sock, addr)
        self.dispatcher = MpdDispatcher(self)

    def on_start(self):
        self.send_lines([u'OK MPD %s' % VERSION])

    def on_line_recieved(self, line):
        self.send_lines(self.dispatcher.handle_request(line))

    def close(self):
        self.stop()
