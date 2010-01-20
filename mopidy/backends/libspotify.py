import logging
import threading

from spotify.manager import SpotifySessionManager
from spotify.alsahelper import AlsaController

from mopidy import config
from mopidy.backends.base import BaseBackend

logger = logging.getLogger(u'backends.libspotify')

class LibspotifySession(SpotifySessionManager, threading.Thread):
    def __init__(self, *args, **kwargs):
        SpotifySessionManager.__init__(self, *args, **kwargs)
        threading.Thread.__init__(self)
        self.audio = AlsaController()

    def run(self):
        self.connect()

    def logged_in(self, session, error):
        logger.info('Logged in')

    def logged_out(self, sess):
        logger.info('Logged out')

    def metadata_updated(self, sess):
        logger.debug('Metadata updated')

    def connection_error(self, sess, error):
        logger.error('Connection error: %s', error)

    def message_to_user(self, sess, message):
        logger.info(message)

    def notify_main_thread(self, sess):
        logger.debug('Notify main thread')

    def music_delivery(self, *args, **kwargs):
        self.audio.music_delivery(*args, **kwargs)

    def play_token_lost(self, sess):
        logger.debug('Play token lost')

    def log_message(self, sess, data):
        logger.debug(data)

    def end_of_track(self, sess):
        logger.debug('End of track')

class LibspotifyBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        self.spotify = LibspotifySession(
            config.SPOTIFY_USERNAME, config.SPOTIFY_PASSWORD)
        logger.info(u'Connecting to Spotify')
        self.spotify.start()
