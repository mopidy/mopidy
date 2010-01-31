import logging
import threading

from spotify.manager import SpotifySessionManager
from spotify.alsahelper import AlsaController

from mopidy import config
from mopidy.backends import BaseBackend

logger = logging.getLogger(u'backends.libspotify')

class LibspotifyBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        super(LibspotifyBackend, self).__init__(*args, **kwargs)
        logger.info(u'Connecting to Spotify')
        self.spotify = LibspotifySession(
            config.SPOTIFY_USERNAME, config.SPOTIFY_PASSWORD)
        self.spotify.start()


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

    def test(self):
        # XXX This should play the first song in your first playlist :-)
        playlist_no = 0
        track_no = 0
        try:
            if not self.queued:
                if len(self.playlists) > playlist_no:
                    playlist = self.playlists[playlist_no]
                    if playlist.is_loaded():
                        if playlist[track_no].is_loaded():
                            session.load(playlist[track_no])
                            session.play(1)
                            self.queued = True
                            logger.info('Playing "%s"',
                                playlist[track_no].name())
        except Exception, e:
            logger.exception(e)

