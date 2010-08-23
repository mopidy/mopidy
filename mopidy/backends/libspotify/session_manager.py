import logging
import os
import threading

from spotify.manager import SpotifySessionManager

from mopidy import get_version, settings
from mopidy.models import Playlist
from mopidy.backends.libspotify.translator import LibspotifyTranslator

logger = logging.getLogger('mopidy.backends.libspotify.session_manager')

class LibspotifySessionManager(SpotifySessionManager, threading.Thread):
    cache_location = os.path.expanduser(settings.SPOTIFY_LIB_CACHE)
    settings_location = os.path.expanduser(settings.SPOTIFY_LIB_CACHE)
    appkey_file = os.path.join(os.path.dirname(__file__), 'spotify_appkey.key')
    user_agent = 'Mopidy %s' % get_version()

    def __init__(self, username, password, core_queue, output):
        SpotifySessionManager.__init__(self, username, password)
        threading.Thread.__init__(self, name='LibspotifySessionManagerThread')
        # Run as a daemon thread, so Mopidy won't wait for this thread to exit
        # before Mopidy exits.
        self.daemon = True
        self.core_queue = core_queue
        self.output = output
        self.connected = threading.Event()
        self.session = None

    def run(self):
        self.connect()

    def logged_in(self, session, error):
        """Callback used by pyspotify"""
        logger.info('Logged in')
        self.session = session
        self.connected.set()

    def logged_out(self, session):
        """Callback used by pyspotify"""
        logger.info('Logged out')

    def metadata_updated(self, session):
        """Callback used by pyspotify"""
        logger.debug('Metadata updated, refreshing stored playlists')
        playlists = []
        for spotify_playlist in session.playlist_container():
            playlists.append(
                LibspotifyTranslator.to_mopidy_playlist(spotify_playlist))
        self.core_queue.put({
            'to': 'output',
            'command': 'set_stored_playlists',
            'playlists': playlists,
        })

    def connection_error(self, session, error):
        """Callback used by pyspotify"""
        logger.error('Connection error: %s', error)

    def message_to_user(self, session, message):
        """Callback used by pyspotify"""
        logger.info(message.strip())

    def notify_main_thread(self, session):
        """Callback used by pyspotify"""
        logger.debug('Notify main thread')

    def music_delivery(self, session, frames, frame_size, num_frames,
            sample_type, sample_rate, channels):
        """Callback used by pyspotify"""
        # TODO Base caps_string on arguments
        caps_string = """
            audio/x-raw-int,
            endianness=(int)1234,
            channels=(int)2,
            width=(int)16,
            depth=(int)16,
            signed=True,
            rate=(int)44100
        """
        self.output.process_message({
            'to': 'output',
            'command': 'deliver_data',
            'caps': caps_string,
            'data': bytes(frames),
        })

    def play_token_lost(self, session):
        """Callback used by pyspotify"""
        logger.debug('Play token lost')
        self.core_queue.put({'command': 'stop_playback'})

    def log_message(self, session, data):
        """Callback used by pyspotify"""
        logger.debug(data.strip())

    def end_of_track(self, session):
        """Callback used by pyspotify"""
        logger.debug('End of data stream.')
        self.output.process_message({
            'to': 'output',
            'command': 'end_of_data_stream',
        })

    def search(self, query, connection):
        """Search method used by Mopidy backend"""
        def callback(results, userdata):
            # TODO Include results from results.albums(), etc. too
            playlist = Playlist(tracks=[
                LibspotifyTranslator.to_mopidy_track(t)
                for t in results.tracks()])
            connection.send(playlist)
        self.connected.wait()
        self.session.search(query, callback)
