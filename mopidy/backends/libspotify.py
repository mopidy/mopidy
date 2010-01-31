import datetime as dt
import logging
import threading

from spotify import Link
from spotify.manager import SpotifySessionManager
from spotify.alsahelper import AlsaController

from mopidy import config
from mopidy.backends import BaseBackend
from mopidy.models import Artist, Album, Track, Playlist

logger = logging.getLogger(u'backends.libspotify')

ENCODING = 'utf-8'

class LibspotifyBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        super(LibspotifyBackend, self).__init__(*args, **kwargs)
        logger.info(u'Connecting to Spotify')
        self.spotify = LibspotifySessionManager(
            config.SPOTIFY_USERNAME, config.SPOTIFY_PASSWORD, backend=self)
        self.spotify.start()

    def update_stored_playlists(self, spotify_playlists):
        logger.info(u'Updating stored playlists')
        playlists = []
        for spotify_playlist in spotify_playlists:
            playlists.append(self._to_mopidy_playlist(spotify_playlist))
        self._playlists = playlists
        logger.debug(u'Available playlists: %s',
            u', '.join([u'<%s>' % p.name for p in self._playlists]))

# Model translation

    def _to_mopidy_id(self, spotify_uri):
        return 0 # TODO

    def _to_mopidy_artist(self, spotify_artist):
        return Artist(
            uri=str(Link.from_artist(spotify_artist)),
            name=spotify_artist.name().decode(ENCODING),
        )

    def _to_mopidy_album(self, spotify_album):
        # TODO pyspotify got much more data on albums than this
        return Album(name=spotify_album.name().decode(ENCODING))

    def _to_mopidy_track(self, spotify_track):
        return Track(
            uri=str(Link.from_track(spotify_track, 0)),
            title=spotify_track.name().decode(ENCODING),
            artists=[self._to_mopidy_artist(a)
                for a in spotify_track.artists()],
            album=self._to_mopidy_album(spotify_track.album()),
            track_no=spotify_track.index(),
            date=dt.date(spotify_track.album().year(), 1, 1),
            length=spotify_track.duration(),
            id=self._to_mopidy_id(str(Link.from_track(spotify_track, 0))),
        )

    def _to_mopidy_playlist(self, spotify_playlist):
        return Playlist(
            uri=str(Link.from_playlist(spotify_playlist)),
            name=spotify_playlist.name().decode(ENCODING),
            tracks=[self._to_mopidy_track(t) for t in spotify_playlist],
        )

# Playback control

    def _load_track(self, uri):
        self.spotify.session.load(Link.from_string(uri).as_track())

    def _play_current_track(self):
        self._load_track(self._current_track.uri)
        self.spotify.session.play(1)

    def _next(self):
        self._current_song_pos += 1
        self._play_current_track()
        return True

    def _pause(self):
        # TODO
        return False

    def _play(self):
        if self._current_track is not None:
            self._play_current_track()
            return True
        else:
            return False

    def _play_id(self, songid):
        self._current_song_pos = songid # XXX
        self._play_current_track()
        return True

    def _play_pos(self, songpos):
        self._current_song_pos = songpos
        self._play_current_track()
        return True

    def _previous(self):
        self._current_song_pos -= 1
        self._play_current_track()
        return True

    def _resume(self):
        # TODO
        return False

    def _stop(self):
        self.spotify.session.play(0)
        return True

# Status querying

    def status_bitrate(self):
        return 320

    def url_handlers(self):
        return [u'spotify:', u'http://open.spotify.com/']


class LibspotifySessionManager(SpotifySessionManager, threading.Thread):
    def __init__(self, username, password, backend):
        SpotifySessionManager.__init__(self, username, password)
        threading.Thread.__init__(self)
        self.backend = backend
        self.audio = AlsaController()

    def run(self):
        self.connect()

    def logged_in(self, session, error):
        logger.info('Logged in')
        self.session = session
        try:
            self.playlists = session.playlist_container()
            logger.debug('Got playlist container')
        except Exception, e:
            logger.exception(e)

    def logged_out(self, session):
        logger.info('Logged out')

    def metadata_updated(self, session):
        logger.debug('Metadata updated')
        self.backend.update_stored_playlists(self.playlists)

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
