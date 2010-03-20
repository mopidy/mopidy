import datetime as dt
import logging
import threading

from spotify import Link
from spotify.manager import SpotifySessionManager
from spotify.alsahelper import AlsaController

from mopidy import settings
from mopidy.backends import (BaseBackend, BaseCurrentPlaylistController,
    BaseLibraryController, BasePlaybackController,
    BaseStoredPlaylistsController)
from mopidy.models import Artist, Album, Track, Playlist

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
        self.translate = LibspotifyTranslator()
        self.spotify = self._connect()

    def _connect(self):
        logger.info(u'Connecting to Spotify')
        spotify = LibspotifySessionManager(
            settings.SPOTIFY_USERNAME, settings.SPOTIFY_PASSWORD, backend=self)
        spotify.start()
        return spotify


class LibspotifyCurrentPlaylistController(BaseCurrentPlaylistController):
    pass


class LibspotifyLibraryController(BaseLibraryController):
    _search_results = None
    _search_results_received = threading.Event()

    def search(self, type, what):
        # FIXME When searching while playing music, this is really slow, like
        # 12-14s between querying and getting results.
        self._search_results_received.clear()
        if type is u'any':
            query = what
        else:
            query = u'%s:%s' % (type, what)
        def callback(results, userdata):
            logger.debug(u'Search results received')
            self._search_results = results
            self._search_results_received.set()
        self.backend.spotify.search(query.encode(ENCODING), callback)
        self._search_results_received.wait()
        result = Playlist(tracks=[self.backend.translate.to_mopidy_track(t)
            for t in self._search_results.tracks()])
        self._search_results = None
        return result

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
    def refresh(self):
        logger.info(u'Refreshing stored playlists')
        playlists = []
        for spotify_playlist in self.backend.spotify.playlists:
            playlists.append(
                self.backend.translate.to_mopidy_playlist(spotify_playlist))
        self._playlists = playlists
        logger.debug(u'Available playlists: %s',
            u', '.join([u'<%s>' % p.name for p in self.playlists]))


class LibspotifyTranslator(object):
    uri_to_id_map = {}
    next_id = 0

    def to_mopidy_id(self, spotify_uri):
        if spotify_uri not in self.uri_to_id_map:
            this_id = self.next_id
            self.next_id += 1
            self.uri_to_id_map[spotify_uri] = this_id
        return self.uri_to_id_map[spotify_uri]

    def to_mopidy_artist(self, spotify_artist):
        if not spotify_artist.is_loaded():
            return Artist(name=u'[loading...]')
        return Artist(
            uri=str(Link.from_artist(spotify_artist)),
            name=spotify_artist.name().decode(ENCODING),
        )

    def to_mopidy_album(self, spotify_album):
        if not spotify_album.is_loaded():
            return Album(name=u'[loading...]')
        # TODO pyspotify got much more data on albums than this
        return Album(name=spotify_album.name().decode(ENCODING))

    def to_mopidy_track(self, spotify_track):
        if not spotify_track.is_loaded():
            return Track(name=u'[loading...]')
        uri = str(Link.from_track(spotify_track, 0))
        return Track(
            uri=uri,
            name=spotify_track.name().decode(ENCODING),
            artists=[self.to_mopidy_artist(a) for a in spotify_track.artists()],
            album=self.to_mopidy_album(spotify_track.album()),
            track_no=spotify_track.index(),
            date=dt.date(spotify_track.album().year(), 1, 1),
            length=spotify_track.duration(),
            bitrate=320,
            id=self.to_mopidy_id(uri),
        )

    def to_mopidy_playlist(self, spotify_playlist):
        if not spotify_playlist.is_loaded():
            return Playlist(name=u'[loading...]')
        return Playlist(
            uri=str(Link.from_playlist(spotify_playlist)),
            name=spotify_playlist.name().decode(ENCODING),
            tracks=[self.to_mopidy_track(t) for t in spotify_playlist],
        )


class LibspotifySessionManager(SpotifySessionManager, threading.Thread):
    def __init__(self, username, password, backend):
        SpotifySessionManager.__init__(self, username, password)
        threading.Thread.__init__(self)
        self.backend = backend
        self.audio = AlsaController()
        self.playlists = []

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
        # XXX This changes data "owned" by another thread, and leads to
        # segmentation fault. We should use locking and messaging here.
        self.backend.stored_playlists.refresh()

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
        self.backend.playback.stop()

    def log_message(self, session, data):
        logger.debug(data)

    def end_of_track(self, session):
        logger.debug('End of track')
        self.backend.playback.next()

    def search(self, query, callback):
        self.session.search(query, callback)
