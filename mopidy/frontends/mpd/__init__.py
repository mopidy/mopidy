import logging
import sys

from pykka import registry, actor

from mopidy import listeners, settings
from mopidy.frontends.mpd import dispatcher, protocol
from mopidy.utils import network, process, log

logger = logging.getLogger('mopidy.frontends.mpd')

class MpdFrontend(actor.ThreadingActor, listeners.BackendListener):
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
            network.Server(hostname, port, protocol=MpdSession)
        except IOError, e:
            logger.error(u'MPD server startup failed: %s', e)
            sys.exit(1)

        logger.info(u'MPD server running at [%s]:%s', hostname, port)

    def on_stop(self):
        process.stop_actors_by_class(MpdSession)

    def send_idle(self, subsystem):
        # FIXME this should be updated once pykka supports non-blocking calls
        # on proxies or some similar solution
        registry.ActorRegistry.broadcast({
            'command': 'pykka_call',
            'attr_path': ('on_idle',),
            'args': [subsystem],
            'kwargs': {},
        }, target_class=MpdSession)

    def playback_state_changed(self):
        self.send_idle('player')

    def playlist_changed(self):
        self.send_idle('playlist')

    def options_changed(self):
        self.send_idle('options')

    def volume_changed(self):
        self.send_idle('mixer')


class MpdSession(network.LineProtocol):
    """
    The MPD client session. Keeps track of a single client session. Any
    requests from the client is passed on to the MPD request dispatcher.
    """

    terminator = protocol.LINE_TERMINATOR
    encoding = protocol.ENCODING

    def __init__(self, connection):
        super(MpdSession, self).__init__(connection)
        self.dispatcher = dispatcher.MpdDispatcher(self)

    def on_start(self):
        logger.info(u'New MPD connection from [%s]:%s', self.host, self.port)
        self.send_lines([u'OK MPD %s' % protocol.VERSION])

    def on_line_received(self, line):
        logger.debug(u'Request from [%s]:%s to %s: %s', self.host, self.port,
            self.actor_urn, line)

        response = self.dispatcher.handle_request(line)
        if not response:
            return

        logger.debug(u'Response to [%s]:%s from %s: %s', self.host, self.port,
            self.actor_urn, log.indent(self.terminator.join(response)))

        self.send_lines(response)

    def on_idle(self, subsystem):
        self.dispatcher.handle_idle(subsystem)

    def close(self):
        self.stop()
