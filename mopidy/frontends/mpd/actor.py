from __future__ import unicode_literals

import logging
import sys

import pykka

from mopidy.core import CoreListener
from mopidy.frontends.mpd import session
from mopidy.utils import encoding, network, process

logger = logging.getLogger('mopidy.frontends.mpd')


class MpdFrontend(pykka.ThreadingActor, CoreListener):
    def __init__(self, config, core):
        super(MpdFrontend, self).__init__()
        hostname = network.format_hostname(config['mpd']['hostname'])
        port = config['mpd']['port']
        self.config_section = config['mpd']
        self.hostname = hostname
        self.port = port

        try:
            network.Server(
                hostname, port,
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

        logger.info('MPD server running at [%s]:%s', hostname, port)

    def on_start(self):
        try:
            if self.config_section['zeroconf_enabled']:
                name = self.config_section['zeroconf_name']

                from mopidy.utils.zeroconf import Zeroconf
                self.service = Zeroconf(
                    stype="_mpd._tcp",
                    name=name, port=self.port, host=self.hostname)
                self.service.publish()

                logger.info('Registered with Avahi as %s', name)
        except Exception as e:
            logger.warning('Avahi registration failed (%s)', e)

    def on_stop(self):
        process.stop_actors_by_class(session.MpdSession)
        try:
            if self.service:
                self.service.unpublish()
        except Exception as e:
            logger.warning('Avahi unregistration failed (%s)', e)

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
