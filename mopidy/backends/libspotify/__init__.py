import datetime as dt
import logging
import os
import multiprocessing
import threading

from spotify import Link, SpotifyError
from spotify.manager import SpotifySessionManager
from spotify.alsahelper import AlsaController

from mopidy import get_version, settings
from mopidy.backends.base import (BaseBackend, BaseCurrentPlaylistController,
    BaseLibraryController, BasePlaybackController,
    BaseStoredPlaylistsController)
from mopidy.models import Artist, Album, Track, Playlist
from mopidy.process import pickle_connection

logger = logging.getLogger('mopidy.backends.libspotify')

ENCODING = 'utf-8'

class LibspotifyBackend(BaseBackend):
    """
    A Spotify backend which uses the official `libspotify library
    <http://developer.spotify.com/en/libspotify/overview/>`_.

    `pyspotify <http://github.com/winjer/pyspotify/>`_ is the Python bindings
    for libspotify. It got no documentation, but multiple examples are
    available. Like libspotify, pyspotify's calls are mostly asynchronous.

    This backend should also work with `openspotify
    <http://github.com/noahwilliamsson/openspotify>`_, but we haven't tested
    that yet.

    **Issues:** http://github.com/jodal/mopidy/issues/labels/backend-libspotify
    """

    def __init__(self, *args, **kwargs):
        super(LibspotifyBackend, self).__init__(*args, **kwargs)
        self.current_playlist = BaseCurrentPlaylistController(backend=self)
        self.library = LibspotifyLibraryController(backend=self)
        self.playback = LibspotifyPlaybackController(backend=self)
        self.stored_playlists = LibspotifyStoredPlaylistsController(
            backend=self)
        self.uri_handlers = [u'spotify:', u'http://open.spotify.com/']
        self.spotify = self._connect()

    def _connect(self):
        logger.info(u'Connecting to Spotify')
        spotify = LibspotifySessionManager(
            settings.SPOTIFY_USERNAME, settings.SPOTIFY_PASSWORD,
            core_queue=self.core_queue,
            output_queue=self.output_queue)
        spotify.start()
        return spotify


class LibspotifyLibraryController(BaseLibraryController):
    def find_exact(self, **query):
        return self.search(**query)

    def lookup(self, uri):
        spotify_track = Link.from_string(uri).as_track()
        return LibspotifyTranslator.to_mopidy_track(spotify_track)

    def refresh(self, uri=None):
        pass # TODO

    def search(self, **query):
        spotify_query = []
        for (field, values) in query.iteritems():
            if not hasattr(values, '__iter__'):
                values = [values]
            for value in values:
                if field == u'track':
                    field = u'title'
                if field == u'any':
                    spotify_query.append(value)
                else:
                    spotify_query.append(u'%s:"%s"' % (field, value))
        spotify_query = u' '.join(spotify_query)
        logger.debug(u'Spotify search query: %s' % spotify_query)
        my_end, other_end = multiprocessing.Pipe()
        self.backend.spotify.search(spotify_query.encode(ENCODING), other_end)
        my_end.poll(None)
        playlist = my_end.recv()
        return playlist


class LibspotifyPlaybackController(BasePlaybackController):
    def _set_output_state(self, state_name):
        logger.debug(u'Setting output state to %s ...', state_name)
        (my_end, other_end) = multiprocessing.Pipe()
        self.backend.output_queue.put({
            'command': 'set_state',
            'state': state_name,
            'reply_to': pickle_connection(other_end),
        })
        my_end.poll(None)
        return my_end.recv()

    def _pause(self):
        return self._set_output_state('PAUSED')

    def _play(self, track):
        self._set_output_state('READY')
        if self.state == self.PLAYING:
            self.stop()
        if track.uri is None:
            return False
        try:
            self.backend.spotify.session.load(
                Link.from_string(track.uri).as_track())
            self.backend.spotify.session.play(1)
            self._set_output_state('PLAYING')
            return True
        except SpotifyError as e:
            logger.warning('Play %s failed: %s', track.uri, e)
            return False

    def _resume(self):
        return self._set_output_state('PLAYING')

    def _seek(self, time_position):
        self._set_output_state('READY')
        result = self.backend.spotify.session.seek(time_position)
        self._set_output_state('PLAYING')

    def _stop(self):
        result = self._set_output_state('READY')
        self.backend.spotify.session.play(0)
        return result


class LibspotifyStoredPlaylistsController(BaseStoredPlaylistsController):
    def create(self, name):
        pass # TODO

    def delete(self, playlist):
        pass # TODO

    def lookup(self, uri):
        pass # TODO

    def refresh(self):
        pass # TODO

    def rename(self, playlist, new_name):
        pass # TODO

    def save(self, playlist):
        pass # TODO


class LibspotifyTranslator(object):
    @classmethod
    def to_mopidy_artist(cls, spotify_artist):
        if not spotify_artist.is_loaded():
            return Artist(name=u'[loading...]')
        return Artist(
            uri=str(Link.from_artist(spotify_artist)),
            name=spotify_artist.name().decode(ENCODING),
        )

    @classmethod
    def to_mopidy_album(cls, spotify_album):
        if not spotify_album.is_loaded():
            return Album(name=u'[loading...]')
        # TODO pyspotify got much more data on albums than this
        return Album(name=spotify_album.name().decode(ENCODING))

    @classmethod
    def to_mopidy_track(cls, spotify_track):
        if not spotify_track.is_loaded():
            return Track(name=u'[loading...]')
        uri = str(Link.from_track(spotify_track, 0))
        if dt.MINYEAR <= int(spotify_track.album().year()) <= dt.MAXYEAR:
            date = dt.date(spotify_track.album().year(), 1, 1)
        else:
            date = None
        return Track(
            uri=uri,
            name=spotify_track.name().decode(ENCODING),
            artists=[cls.to_mopidy_artist(a) for a in spotify_track.artists()],
            album=cls.to_mopidy_album(spotify_track.album()),
            track_no=spotify_track.index(),
            date=date,
            length=spotify_track.duration(),
            bitrate=320,
        )

    @classmethod
    def to_mopidy_playlist(cls, spotify_playlist):
        if not spotify_playlist.is_loaded():
            return Playlist(name=u'[loading...]')
        return Playlist(
            uri=str(Link.from_playlist(spotify_playlist)),
            name=spotify_playlist.name().decode(ENCODING),
            tracks=[cls.to_mopidy_track(t) for t in spotify_playlist],
        )

class LibspotifySessionManager(SpotifySessionManager, threading.Thread):
    cache_location = os.path.expanduser(settings.SPOTIFY_LIB_CACHE)
    settings_location = os.path.expanduser(settings.SPOTIFY_LIB_CACHE)
    appkey_file = os.path.expanduser(settings.SPOTIFY_LIB_APPKEY)
    user_agent = 'Mopidy %s' % get_version()

    def __init__(self, username, password, core_queue, output_queue):
        SpotifySessionManager.__init__(self, username, password)
        threading.Thread.__init__(self)
        self.core_queue = core_queue
        self.output_queue = output_queue
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
            'command': 'set_stored_playlists',
            'playlists': playlists,
        })

    def connection_error(self, session, error):
        """Callback used by pyspotify"""
        logger.error('Connection error: %s', error)

    def message_to_user(self, session, message):
        """Callback used by pyspotify"""
        logger.info(message)

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
        self.output_queue.put({
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
        logger.debug(data)

    def end_of_track(self, session):
        """Callback used by pyspotify"""
        logger.debug('End of data stream.')
        self.output_queue.put({'command': 'end_of_data_stream'})

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
