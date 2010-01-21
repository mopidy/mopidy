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
        self.queued = False

    def run(self):
        self.connect()

    def logged_in(self, session, error):
        logger.info('Logged in')
        try:
            self.playlists = session.playlist_container()
            logger.debug('Got playlist container')
        except Exception, e:
            logger.exception(e)

    def logged_out(self, session):
        logger.info('Logged out')

    def metadata_updated(self, session):
        logger.debug('Metadata updated')

        # XXX This should play the first song in your first playlist :-)
        try:
            if not self.queued:
                playlist = self.playlists[0]
                if playlist.is_loaded():
                    if playlist[0].is_loaded():
                        session.load(playlist[0])
                        session.play(1)
                        self.queued = True
                        logger.info('Playing "%s"', playlist[0].name())
        except Exception, e:
            logger.exception(e)

    def connection_error(self, session, error):
        logger.error('Connection error: %s', error)

    def message_to_user(self, session, message):
        logger.info(message)

    def notify_main_thread(self, session):
        logger.debug('Notify main thread')

    def music_delivery(self, *args, **kwargs):
        self.audio.music_delivery(*args, **kwargs)

    def play_token_lost(self, session):
        logger.debug('Play token lost')

    def log_message(self, session, data):
        logger.debug(data)

    def end_of_track(self, session):
        logger.debug('End of track')

class LibspotifyBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        self.spotify = LibspotifySession(
            config.SPOTIFY_USERNAME, config.SPOTIFY_PASSWORD)
        logger.info(u'Connecting to Spotify')
        self.spotify.start()
