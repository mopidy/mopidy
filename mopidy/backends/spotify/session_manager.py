from __future__ import unicode_literals

import pygst
pygst.require('0.10')
import gst

import logging
import os
import threading

from spotify.manager import SpotifySessionManager as PyspotifySessionManager

from mopidy import audio, settings
from mopidy.backends.listener import BackendListener
from mopidy.utils import process, versioning

from . import translator
from .container_manager import SpotifyContainerManager
from .playlist_manager import SpotifyPlaylistManager

logger = logging.getLogger('mopidy.backends.spotify')

BITRATES = {96: 2, 160: 0, 320: 1}

# pylint: disable = R0901
# SpotifySessionManager: Too many ancestors (9/7)


class SpotifySessionManager(process.BaseThread, PyspotifySessionManager):
    cache_location = settings.SPOTIFY_CACHE_PATH
    settings_location = cache_location
    appkey_file = os.path.join(os.path.dirname(__file__), 'spotify_appkey.key')
    user_agent = 'Mopidy %s' % versioning.get_version()

    def __init__(self, username, password, audio, backend_ref, proxy=None,
                 proxy_username=None, proxy_password=None):
        PyspotifySessionManager.__init__(
            self, username, password, proxy=proxy,
            proxy_username=proxy_username,
            proxy_password=proxy_password)
        process.BaseThread.__init__(self)
        self.name = 'SpotifyThread'

        self.audio = audio
        self.backend = None
        self.backend_ref = backend_ref

        self.connected = threading.Event()

        self.container_manager = None
        self.playlist_manager = None

        self._initial_data_receive_completed = False

    def run_inside_try(self):
        self.backend = self.backend_ref.proxy()
        self.connect()

    def logged_in(self, session, error):
        """Callback used by pyspotify"""
        if error:
            logger.error('Spotify login error: %s', error)
            return

        logger.info('Connected to Spotify')

        # To work with both pyspotify 1.9 and 1.10
        if not hasattr(self, 'session'):
            self.session = session

        logger.debug(
            'Preferred Spotify bitrate is %s kbps',
            settings.SPOTIFY_BITRATE)
        session.set_preferred_bitrate(BITRATES[settings.SPOTIFY_BITRATE])

        self.container_manager = SpotifyContainerManager(self)
        self.playlist_manager = SpotifyPlaylistManager(self)

        self.container_manager.watch(session.playlist_container())

        self.connected.set()

    def logged_out(self, session):
        """Callback used by pyspotify"""
        logger.info('Disconnected from Spotify')
        self.connected.clear()

    def metadata_updated(self, session):
        """Callback used by pyspotify"""
        logger.debug('Callback called: Metadata updated')

    def connection_error(self, session, error):
        """Callback used by pyspotify"""
        if error is None:
            logger.info('Spotify connection OK')
        else:
            logger.error('Spotify connection error: %s', error)
            if self.audio.state.get() == audio.PlaybackState.PLAYING:
                self.backend.playback.pause()

    def message_to_user(self, session, message):
        """Callback used by pyspotify"""
        logger.debug('User message: %s', message.strip())

    def music_delivery(self, session, frames, frame_size, num_frames,
                       sample_type, sample_rate, channels):
        """Callback used by pyspotify"""
        # pylint: disable = R0913
        # Too many arguments (8/5)
        assert sample_type == 0, 'Expects 16-bit signed integer samples'
        capabilites = """
            audio/x-raw-int,
            endianness=(int)1234,
            channels=(int)%(channels)d,
            width=(int)16,
            depth=(int)16,
            signed=(boolean)true,
            rate=(int)%(sample_rate)d
        """ % {
            'sample_rate': sample_rate,
            'channels': channels,
        }
        buffer_ = gst.Buffer(bytes(frames))
        buffer_.set_caps(gst.caps_from_string(capabilites))

        if self.audio.emit_data(buffer_).get():
            return num_frames
        else:
            return 0

    def play_token_lost(self, session):
        """Callback used by pyspotify"""
        logger.debug('Play token lost')
        self.backend.playback.pause()

    def log_message(self, session, data):
        """Callback used by pyspotify"""
        logger.debug('System message: %s' % data.strip())
        if 'offline-mgr' in data and 'files unlocked' in data:
            # XXX This is a very very fragile and ugly hack, but we get no
            # proper event when libspotify is done with initial data loading.
            # We delay the expensive refresh of Mopidy's playlists until this
            # message arrives. This way, we avoid doing the refresh once for
            # every playlist or other change. This reduces the time from
            # startup until the Spotify backend is ready from 35s to 12s in one
            # test with clean Spotify cache. In cases with an outdated cache
            # the time improvements should be a lot greater.
            if not self._initial_data_receive_completed:
                self._initial_data_receive_completed = True
                self.refresh_playlists()

    def end_of_track(self, session):
        """Callback used by pyspotify"""
        logger.debug('End of data stream reached')
        self.audio.emit_end_of_stream()

    def refresh_playlists(self):
        """Refresh the playlists in the backend with data from Spotify"""
        if not self._initial_data_receive_completed:
            logger.debug('Still getting data; skipped refresh of playlists')
            return
        playlists = map(
            translator.to_mopidy_playlist, self.session.playlist_container())
        playlists = filter(None, playlists)
        self.backend.playlists.playlists = playlists
        logger.info('Loaded %d Spotify playlist(s)', len(playlists))
        BackendListener.send('playlists_loaded')

    def logout(self):
        """Log out from spotify"""
        logger.debug('Logging out from Spotify')

        # To work with both pyspotify 1.9 and 1.10
        if getattr(self, 'session', None):
            self.session.logout()
