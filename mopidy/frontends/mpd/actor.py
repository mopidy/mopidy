from __future__ import unicode_literals

import logging
import sys

import pykka

from mopidy.core import CoreListener
from mopidy.frontends.mpd import session
from mopidy.utils import encoding, network, process, zeroconf

logger = logging.getLogger('mopidy.frontends.mpd')


class MpdFrontend(pykka.ThreadingActor, CoreListener):
    def __init__(self, config, core):
        super(MpdFrontend, self).__init__()

        hostname = network.format_hostname(config['mpd']['hostname'])
        self.hostname = hostname
        self.port = config['mpd']['port']
        self.zeroconf_name = config['mpd']['zeroconf']
        self.zeroconf_service = None

        try:
            network.Server(
                self.hostname, self.port,
                protocol=session.MpdSession,
                protocol_kwargs={
                    'config': config,
                    'core': core,
                },
                max_connections=config['mpd']['max_connections'],
                timeout=config['mpd']['connection_timeout'])
        except IOError as error:
            logger.error(
                'MPD server startup failed: %s',
                encoding.locale_decode(error))
            sys.exit(1)

        logger.info('MPD server running at [%s]:%s', self.hostname, self.port)

    def on_start(self):
        if self.zeroconf_name:
            self.zeroconf_service = zeroconf.Zeroconf(
                stype='_mpd._tcp', name=self.zeroconf_name,
                host=self.hostname, port=self.port)

            if self.zeroconf_service.publish():
                logger.info('Registered MPD with Zeroconf as "%s"',
                            self.zeroconf_service.name)
            else:
                logger.warning('Registering MPD with Zeroconf failed.')

    def on_stop(self):
        if self.zeroconf_service:
            self.zeroconf_service.unpublish()

        process.stop_actors_by_class(session.MpdSession)

    def send_idle(self, subsystem):
        listeners = pykka.ActorRegistry.get_by_class(session.MpdSession)
        for listener in listeners:
            getattr(listener.proxy(), 'on_idle')(subsystem)

    def playback_state_changed(self, old_state, new_state):
        self.send_idle('player')

    def tracklist_changed(self):
        self.send_idle('playlist')

    def options_changed(self):
        self.send_idle('options')

    def volume_changed(self, volume):
        self.send_idle('mixer')

    def mute_changed(self, mute):
        self.send_idle('output')
