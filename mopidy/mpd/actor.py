from __future__ import absolute_import, unicode_literals

import logging

import pykka

from mopidy import exceptions, zeroconf
from mopidy.core import CoreListener
from mopidy.mpd import session, uri_mapper
from mopidy.utils import encoding, network, process

logger = logging.getLogger(__name__)


class MpdFrontend(pykka.ThreadingActor, CoreListener):
    def __init__(self, config, core):
        super(MpdFrontend, self).__init__()

        self.hostname = network.format_hostname(config['mpd']['hostname'])
        self.port = config['mpd']['port']
        self.uri_map = uri_mapper.MpdUriMapper(core)

        self.zeroconf_name = config['mpd']['zeroconf']
        self.zeroconf_service = None

        try:
            network.Server(
                self.hostname, self.port,
                protocol=session.MpdSession,
                protocol_kwargs={
                    'config': config,
                    'core': core,
                    'uri_map': self.uri_map,
                },
                max_connections=config['mpd']['max_connections'],
                timeout=config['mpd']['connection_timeout'])
        except IOError as error:
            raise exceptions.FrontendError(
                'MPD server startup failed: %s' %
                encoding.locale_decode(error))

        logger.info('MPD server running at [%s]:%s', self.hostname, self.port)

    def on_start(self):
        if self.zeroconf_name:
            self.zeroconf_service = zeroconf.Zeroconf(
                stype='_mpd._tcp', name=self.zeroconf_name,
                port=self.port)
            self.zeroconf_service.publish()

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

    def stream_title_changed(self, title):
        self.send_idle('playlist')
