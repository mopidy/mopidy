import datetime as dt
import logging
import os
import multiprocessing
import threading

from spotify import Link
from spotify.manager import SpotifySessionManager
from spotify.alsahelper import AlsaController

from mopidy import get_version, settings
from mopidy.backends import (BaseBackend, BaseCurrentPlaylistController,
    BaseLibraryController, BasePlaybackController,
    BaseStoredPlaylistsController)
from mopidy.models import Artist, Album, Track, Playlist
from mopidy.utils import spotify_uri_to_int

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

    **Issues**

    - libspotify is badly packaged. See
      http://getsatisfaction.com/spotify/topics/libspotify_please_fix_the_installation_script.
    """

    def __init__(self, *args, **kwargs):
        super(LibspotifyBackend, self).__init__(*args, **kwargs)
        self.current_playlist = LibspotifyCurrentPlaylistController(
            backend=self)
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
            core_queue=self.core_queue)
        spotify.start()
        return spotify


class LibspotifyCurrentPlaylistController(BaseCurrentPlaylistController):
    pass


class LibspotifyLibraryController(BaseLibraryController):
    def search(self, type, what):
        if type is u'any':
            query = what
        else:
            query = u'%s:%s' % (type, what)
        my_end, other_end = multiprocessing.Pipe()
        self.backend.spotify.search(query.encode(ENCODING), other_end)
        my_end.poll(None)
        logger.debug(u'In search method, receiving search results')
        playlist = my_end.recv()
        logger.debug(u'In search method, done receiving search results')
        logger.debug(['%s' % t.name for t in playlist.tracks])
        return playlist

    find_exact = search


class LibspotifyPlaybackController(BasePlaybackController):
    def _pause(self):
        # TODO
        return False

    def _play(self, track):
        if self.state == self.PLAYING:
            self.stop()
        if track.uri is None:
            return False
        self.backend.spotify.session.load(
            Link.from_string(track.uri).as_track())
        self.backend.spotify.session.play(1)
        return True

    def _resume(self):
        # TODO
        return False

    def _stop(self):
        self.backend.spotify.session.play(0)
        return True


class LibspotifyStoredPlaylistsController(BaseStoredPlaylistsController):
    pass


class LibspotifyTranslator(object):
    @classmethod
    def to_mopidy_id(cls, spotify_uri):
        return spotify_uri_to_int(spotify_uri)

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
        return Track(
            uri=uri,
            name=spotify_track.name().decode(ENCODING),
            artists=[cls.to_mopidy_artist(a) for a in spotify_track.artists()],
            album=cls.to_mopidy_album(spotify_track.album()),
            track_no=spotify_track.index(),
            date=dt.date(spotify_track.album().year(), 1, 1),
            length=spotify_track.duration(),
            bitrate=320,
            id=cls.to_mopidy_id(uri),
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

    def __init__(self, username, password, core_queue):
        SpotifySessionManager.__init__(self, username, password)
        threading.Thread.__init__(self)
        self.core_queue = core_queue
        self.connected = threading.Event()
        self.audio = AlsaController()

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

    def music_delivery(self, *args, **kwargs):
        """Callback used by pyspotify"""
        self.audio.music_delivery(*args, **kwargs)

    def play_token_lost(self, session):
        """Callback used by pyspotify"""
        logger.debug('Play token lost')
        self.core_queue.put({'command': 'stop_playback'})

    def log_message(self, session, data):
        """Callback used by pyspotify"""
        logger.debug(data)

    def end_of_track(self, session):
        """Callback used by pyspotify"""
        logger.debug('End of track')
        self.core_queue.put({'command': 'end_of_track'})

    def search(self, query, connection):
        """Search method used by Mopidy backend"""
        self.connected.wait()
        def callback(results, userdata):
            logger.debug(u'In search callback, translating search results')
            logger.debug(results.tracks())
            # TODO Include results from results.albums(), etc. too
            playlist = Playlist(tracks=[
                LibspotifyTranslator.to_mopidy_track(t)
                for t in results.tracks()])
            logger.debug(u'In search callback, sending search results')
            logger.debug(['%s' % t.name for t in playlist.tracks])
            connection.send(playlist)
        self.session.search(query, callback)
