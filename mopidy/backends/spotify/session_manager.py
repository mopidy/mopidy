import logging
import os
import threading

from spotify.manager import SpotifySessionManager as PyspotifySessionManager

from pykka.registry import ActorRegistry

from mopidy import audio, get_version, settings
from mopidy.backends.base import Backend
from mopidy.backends.spotify import BITRATES
from mopidy.backends.spotify.container_manager import SpotifyContainerManager
from mopidy.backends.spotify.playlist_manager import SpotifyPlaylistManager
from mopidy.backends.spotify.translator import SpotifyTranslator
from mopidy.models import Playlist
from mopidy.utils.process import BaseThread

logger = logging.getLogger('mopidy.backends.spotify.session_manager')

# pylint: disable = R0901
# SpotifySessionManager: Too many ancestors (9/7)


class SpotifySessionManager(BaseThread, PyspotifySessionManager):
    cache_location = settings.SPOTIFY_CACHE_PATH
    settings_location = cache_location
    appkey_file = os.path.join(os.path.dirname(__file__), 'spotify_appkey.key')
    user_agent = 'Mopidy %s' % get_version()

    def __init__(self, username, password):
        PyspotifySessionManager.__init__(self, username, password)
        BaseThread.__init__(self)
        self.name = 'SpotifyThread'

        self.audio = None
        self.backend = None

        self.connected = threading.Event()
        self.session = None

        self.container_manager = None
        self.playlist_manager = None

        self._initial_data_receive_completed = False

    def run_inside_try(self):
        self.setup()
        self.connect()

    def setup(self):
        audio_refs = ActorRegistry.get_by_class(audio.Audio)
        assert len(audio_refs) == 1, \
            'Expected exactly one running Audio instance.'
        self.audio = audio_refs[0].proxy()

        backend_refs = ActorRegistry.get_by_class(Backend)
        assert len(backend_refs) == 1, 'Expected exactly one running backend.'
        self.backend = backend_refs[0].proxy()

    def logged_in(self, session, error):
        """Callback used by pyspotify"""
        if error:
            logger.error(u'Spotify login error: %s', error)
            return

        logger.info(u'Connected to Spotify')
        self.session = session

        logger.debug(u'Preferred Spotify bitrate is %s kbps',
            settings.SPOTIFY_BITRATE)
        self.session.set_preferred_bitrate(BITRATES[settings.SPOTIFY_BITRATE])

        self.container_manager = SpotifyContainerManager(self)
        self.playlist_manager = SpotifyPlaylistManager(self)

        self.container_manager.watch(self.session.playlist_container())

        self.connected.set()

    def logged_out(self, session):
        """Callback used by pyspotify"""
        logger.info(u'Disconnected from Spotify')

    def metadata_updated(self, session):
        """Callback used by pyspotify"""
        logger.debug(u'Callback called: Metadata updated')

    def connection_error(self, session, error):
        """Callback used by pyspotify"""
        if error is None:
            logger.info(u'Spotify connection OK')
        else:
            logger.error(u'Spotify connection error: %s', error)
            self.backend.playback.pause()

    def message_to_user(self, session, message):
        """Callback used by pyspotify"""
        logger.debug(u'User message: %s', message.strip())

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
        self.audio.emit_data(capabilites, bytes(frames))
        return num_frames

    def play_token_lost(self, session):
        """Callback used by pyspotify"""
        logger.debug(u'Play token lost')
        self.backend.playback.pause()

    def log_message(self, session, data):
        """Callback used by pyspotify"""
        logger.debug(u'System message: %s' % data.strip())
        if 'offline-mgr' in data and 'files unlocked' in data:
            # XXX This is a very very fragile and ugly hack, but we get no
            # proper event when libspotify is done with initial data loading.
            # We delay the expensive refresh of Mopidy's stored playlists until
            # this message arrives. This way, we avoid doing the refresh once
            # for every playlist or other change. This reduces the time from
            # startup until the Spotify backend is ready from 35s to 12s in one
            # test with clean Spotify cache. In cases with an outdated cache
            # the time improvements should be a lot better.
            self._initial_data_receive_completed = True
            self.refresh_stored_playlists()

    def end_of_track(self, session):
        """Callback used by pyspotify"""
        logger.debug(u'End of data stream reached')
        self.audio.emit_end_of_stream()

    def refresh_stored_playlists(self):
        """Refresh the stored playlists in the backend with fresh meta data
        from Spotify"""
        if not self._initial_data_receive_completed:
            logger.debug(u'Still getting data; skipped refresh of playlists')
            return
        playlists = map(SpotifyTranslator.to_mopidy_playlist,
            self.session.playlist_container())
        playlists = filter(None, playlists)
        self.backend.stored_playlists.playlists = playlists
        logger.info(u'Loaded %d Spotify playlist(s)', len(playlists))

    def search(self, query, queue):
        """Search method used by Mopidy backend"""
        def callback(results, userdata=None):
            # TODO Include results from results.albums(), etc. too
            # TODO Consider launching a second search if results.total_tracks()
            # is larger than len(results.tracks())
            playlist = Playlist(tracks=[
                SpotifyTranslator.to_mopidy_track(t)
                for t in results.tracks()])
            queue.put(playlist)
        self.connected.wait()
        self.session.search(query, callback, track_count=100,
            album_count=0, artist_count=0)

    def logout(self):
        """Log out from spotify"""
        logger.debug(u'Logging out from Spotify')
        if self.session:
            self.session.logout()
