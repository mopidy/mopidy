import logging
import sys

from pykka import registry, actor

from mopidy import settings
from mopidy.core import CoreListener
from mopidy.frontends.mpd import session
from mopidy.utils import encoding, network, process

logger = logging.getLogger('mopidy.frontends.mpd')


class MpdFrontend(actor.ThreadingActor, CoreListener):
    """
    The MPD frontend.

    **Dependencies:**

    - None

    **Settings:**

    - :attr:`mopidy.settings.MPD_SERVER_HOSTNAME`
    - :attr:`mopidy.settings.MPD_SERVER_PORT`
    - :attr:`mopidy.settings.MPD_SERVER_PASSWORD`
    """

    def __init__(self, core):
        super(MpdFrontend, self).__init__()
        hostname = network.format_hostname(settings.MPD_SERVER_HOSTNAME)
        port = settings.MPD_SERVER_PORT

        try:
            network.Server(
                hostname, port,
                protocol=session.MpdSession, protocol_kwargs={'core': core},
                max_connections=settings.MPD_SERVER_MAX_CONNECTIONS)
        except IOError as error:
            logger.error(
                u'MPD server startup failed: %s',
                encoding.locale_decode(error))
            sys.exit(1)

        logger.info(u'MPD server running at [%s]:%s', hostname, port)

    def on_stop(self):
        process.stop_actors_by_class(session.MpdSession)

    def send_idle(self, subsystem):
        # FIXME this should be updated once pykka supports non-blocking calls
        # on proxies or some similar solution
        registry.ActorRegistry.broadcast({
            'command': 'pykka_call',
            'attr_path': ('on_idle',),
            'args': [subsystem],
            'kwargs': {},
        }, target_class=session.MpdSession)

    def playback_state_changed(self, old_state, new_state):
        self.send_idle('player')

    def playlist_changed(self):
        self.send_idle('playlist')

    def options_changed(self):
        self.send_idle('options')

    def volume_changed(self):
        self.send_idle('mixer')
