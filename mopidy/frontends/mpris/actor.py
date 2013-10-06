from __future__ import unicode_literals

import logging
import os

import pykka

from mopidy.core import CoreListener
from mopidy.frontends.mpris import objects

logger = logging.getLogger('mopidy.frontends.mpris')

try:
    indicate = None
    if 'DISPLAY' in os.environ:
        import indicate
except ImportError:
    pass

if indicate is None:
    logger.debug('Startup notification will not be sent')


class MprisFrontend(pykka.ThreadingActor, CoreListener):
    def __init__(self, config, core):
        super(MprisFrontend, self).__init__()
        self.config = config
        self.core = core
        self.indicate_server = None
        self.mpris_object = None

    def on_start(self):
        try:
            self.mpris_object = objects.MprisObject(self.config, self.core)
            self._send_startup_notification()
        except Exception as e:
            logger.warning('MPRIS frontend setup failed (%s)', e)
            self.stop()

    def on_stop(self):
        logger.debug('Removing MPRIS object from D-Bus connection...')
        if self.mpris_object:
            self.mpris_object.remove_from_connection()
            self.mpris_object = None
        logger.debug('Removed MPRIS object from D-Bus connection')

    def _send_startup_notification(self):
        """
        Send startup notification using libindicate to make Mopidy appear in
        e.g. `Ubunt's sound menu <https://wiki.ubuntu.com/SoundMenu>`_.

        A reference to the libindicate server is kept for as long as Mopidy is
        running. When Mopidy exits, the server will be unreferenced and Mopidy
        will automatically be unregistered from e.g. the sound menu.
        """
        if not indicate:
            return
        logger.debug('Sending startup notification...')
        self.indicate_server = indicate.Server()
        self.indicate_server.set_type('music.mopidy')
        self.indicate_server.set_desktop_file(
            self.config['mpris']['desktop_file'])
        self.indicate_server.show()
        logger.debug('Startup notification sent')

    def _emit_properties_changed(self, interface, changed_properties):
        if self.mpris_object is None:
            return
        props_with_new_values = [
            (p, self.mpris_object.Get(interface, p))
            for p in changed_properties]
        self.mpris_object.PropertiesChanged(
            interface, dict(props_with_new_values), [])

    def track_playback_paused(self, tl_track, time_position):
        logger.debug('Received track_playback_paused event')
        self._emit_properties_changed(objects.PLAYER_IFACE, ['PlaybackStatus'])

    def track_playback_resumed(self, tl_track, time_position):
        logger.debug('Received track_playback_resumed event')
        self._emit_properties_changed(objects.PLAYER_IFACE, ['PlaybackStatus'])

    def track_playback_started(self, tl_track):
        logger.debug('Received track_playback_started event')
        self._emit_properties_changed(
            objects.PLAYER_IFACE, ['PlaybackStatus', 'Metadata'])

    def track_playback_ended(self, tl_track, time_position):
        logger.debug('Received track_playback_ended event')
        self._emit_properties_changed(
            objects.PLAYER_IFACE, ['PlaybackStatus', 'Metadata'])

    def volume_changed(self, volume):
        logger.debug('Received volume_changed event')
        self._emit_properties_changed(objects.PLAYER_IFACE, ['Volume'])

    def seeked(self, time_position_in_ms):
        logger.debug('Received seeked event')
        self.mpris_object.Seeked(time_position_in_ms * 1000)

    def playlists_loaded(self):
        logger.debug('Received playlists_loaded event')
        self._emit_properties_changed(
            objects.PLAYLISTS_IFACE, ['PlaylistCount'])

    def playlist_changed(self, playlist):
        logger.debug('Received playlist_changed event')
        playlist_id = self.mpris_object.get_playlist_id(playlist.uri)
        playlist = (playlist_id, playlist.name, '')
        self.mpris_object.PlaylistChanged(playlist)
