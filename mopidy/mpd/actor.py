from __future__ import absolute_import, unicode_literals

import logging

import pykka

from mopidy import exceptions, listener, zeroconf
from mopidy.core import CoreListener
from mopidy.internal import encoding, network, process
from mopidy.mpd import session, uri_mapper

logger = logging.getLogger(__name__)

_CORE_EVENTS_TO_IDLE_SUBSYSTEMS = {
    'track_playback_paused': None,
    'track_playback_resumed': None,
    'track_playback_started': None,
    'track_playback_ended': None,
    'playback_state_changed': 'player',
    'tracklist_changed': 'playlist',
    'playlists_loaded': 'stored_playlist',
    'playlist_changed': 'stored_playlist',
    'playlist_deleted': 'stored_playlist',
    'options_changed': 'options',
    'volume_changed': 'mixer',
    'mute_changed': 'output',
    'seeked': 'player',
    'stream_title_changed': 'playlist',
}


class MpdFrontend(pykka.ThreadingActor, CoreListener):

    def __init__(self, config, core):
        super(MpdFrontend, self).__init__()

        self.hostname = network.format_hostname(config['mpd']['hostname'])
        self.port = config['mpd']['port']
        self.uri_map = uri_mapper.MpdUriMapper(core)

        self.zeroconf_name = config['mpd']['zeroconf']
        self.zeroconf_service = None

        self._setup_server(config, core)

    def _setup_server(self, config, core):
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
                name=self.zeroconf_name,
                stype='_mpd._tcp',
                port=self.port)
            self.zeroconf_service.publish()

    def on_stop(self):
        if self.zeroconf_service:
            self.zeroconf_service.unpublish()

        process.stop_actors_by_class(session.MpdSession)

    def on_event(self, event, **kwargs):
        if event not in _CORE_EVENTS_TO_IDLE_SUBSYSTEMS:
            logger.warning(
                'Got unexpected event: %s(%s)', event, ', '.join(kwargs))
        else:
            self.send_idle(_CORE_EVENTS_TO_IDLE_SUBSYSTEMS[event])

    def send_idle(self, subsystem):
        if subsystem:
            listener.send(session.MpdSession, subsystem)
