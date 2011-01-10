import logging
import os
import threading

import spotify.manager

from mopidy import get_version, settings
from mopidy.backends.spotify.translator import SpotifyTranslator
from mopidy.models import Playlist
from mopidy.utils.process import BaseThread

logger = logging.getLogger('mopidy.backends.spotify.session_manager')

# pylint: disable = R0901
# SpotifySessionManager: Too many ancestors (9/7)

class SpotifySessionManager(spotify.manager.SpotifySessionManager, BaseThread):
    cache_location = settings.SPOTIFY_CACHE_PATH
    settings_location = settings.SPOTIFY_CACHE_PATH
    appkey_file = os.path.join(os.path.dirname(__file__), 'spotify_appkey.key')
    user_agent = 'Mopidy %s' % get_version()

    def __init__(self, username, password, core_queue, output):
        spotify.manager.SpotifySessionManager.__init__(
            self, username, password)
        BaseThread.__init__(self, core_queue)
        self.name = 'SpotifySMThread'
        self.output = output
        self.connected = threading.Event()
        self.session = None

    def run_inside_try(self):
        self.connect()

    def logged_in(self, session, error):
        """Callback used by pyspotify"""
        logger.info(u'Connected to Spotify')
        self.session = session
        if settings.SPOTIFY_HIGH_BITRATE:
            logger.debug(u'Prefer high bitrate')
            self.session.set_preferred_bitrate(1)
        else:
            logger.debug(u'Prefer normal bitrate')
            self.session.set_preferred_bitrate(0)
        self.connected.set()

    def logged_out(self, session):
        """Callback used by pyspotify"""
        logger.info(u'Disconnected from Spotify')

    def metadata_updated(self, session):
        """Callback used by pyspotify"""
        logger.debug(u'Metadata updated, refreshing stored playlists')
        playlists = []
        for spotify_playlist in session.playlist_container():
            playlists.append(
                SpotifyTranslator.to_mopidy_playlist(spotify_playlist))
        playlists = filter(None, playlists)
        self.core_queue.put({
            'command': 'set_stored_playlists',
            'playlists': playlists,
        })

    def connection_error(self, session, error):
        """Callback used by pyspotify"""
        logger.error(u'Connection error: %s', error)

    def message_to_user(self, session, message):
        """Callback used by pyspotify"""
        logger.debug(u'User message: %s', message.strip())

    def notify_main_thread(self, session):
        """Callback used by pyspotify"""
        logger.debug(u'notify_main_thread() called')

    def music_delivery(self, session, frames, frame_size, num_frames,
            sample_type, sample_rate, channels):
        """Callback used by pyspotify"""
        # pylint: disable = R0913
        # Too many arguments (8/5)
        assert sample_type == 0, u'Expects 16-bit signed integer samples'
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
        self.output.deliver_data(capabilites, bytes(frames))

    def play_token_lost(self, session):
        """Callback used by pyspotify"""
        logger.debug(u'Play token lost')
        self.core_queue.put({'command': 'stop_playback'})

    def log_message(self, session, data):
        """Callback used by pyspotify"""
        logger.debug(u'System message: %s' % data.strip())

    def end_of_track(self, session):
        """Callback used by pyspotify"""
        logger.debug(u'End of data stream reached')
        self.output.end_of_data_stream()

    def search(self, query, connection):
        """Search method used by Mopidy backend"""
        def callback(results, userdata=None):
            # TODO Include results from results.albums(), etc. too
            playlist = Playlist(tracks=[
                SpotifyTranslator.to_mopidy_track(t)
                for t in results.tracks()])
            connection.send(playlist)
        self.connected.wait()
        self.session.search(query, callback)
