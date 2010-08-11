import datetime as dt
import gobject
import logging
import os
import multiprocessing
import threading

import pygst
pygst.require('0.10')
import gst

from spotify import Link, SpotifyError
from spotify.manager import SpotifySessionManager
from spotify.alsahelper import AlsaController

from mopidy import get_version, settings
from mopidy.backends.base import (BaseBackend, BaseCurrentPlaylistController,
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
        self.gstreamer_pipeline = gst.Pipeline("spotify_pipeline")
        self.spotify = self._connect()

    def _connect(self):
        logger.info(u'Connecting to Spotify')
        spotify = LibspotifySessionManager(
            settings.SPOTIFY_USERNAME, settings.SPOTIFY_PASSWORD,
            core_queue=self.core_queue,
            gstreamer_pipeline=self.gstreamer_pipeline)
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
        logger.debug(u'In search method, search for: %s' % spotify_query)
        my_end, other_end = multiprocessing.Pipe()
        self.backend.spotify.search(spotify_query.encode(ENCODING), other_end)
        logger.debug(u'In Library.search(), waiting for search results')
        my_end.poll(None)
        logger.debug(u'In Library.search(), receiving search results')
        playlist = my_end.recv()
        logger.debug(u'In Library.search(), done receiving search results')
        logger.debug(['%s' % t.name for t in playlist.tracks])
        return playlist


class LibspotifyPlaybackController(BasePlaybackController):
    def _pause(self):
        result = self.backend.gstreamer_pipeline.set_state(gst.STATE_PAUSED)
        logger.debug('Changed gstreamer state to paused. Result was: %s' % result)
        return result == gst.STATE_CHANGE_SUCCESS

    def _play(self, track):
        self.backend.gstreamer_pipeline.set_state(gst.STATE_READY)
        if self.state == self.PLAYING:
            self.stop()
        if track.uri is None:
            return False
        try:
            self.backend.spotify.session.load(
                Link.from_string(track.uri).as_track())
            self.backend.spotify.session.play(1)
            self.backend.gstreamer_pipeline.set_state(gst.STATE_PLAYING)
            return True
        except SpotifyError as e:
            logger.warning('Play %s failed: %s', track.uri, e)
            return False

    def _resume(self):
        result = self.backend.gstreamer_pipeline.set_state(gst.STATE_PLAYING)
        logger.debug('Changed gstreamer state to playing. Result was: %s' % result)
        return result == gst.STATE_CHANGE_SUCCESS

    def _seek(self, time_position):
        pass # TODO

    def _stop(self):
        self.backend.gstreamer_pipeline.set_state(gst.STATE_READY)
        self.backend.spotify.session.play(0)
        return True


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

    def search(self, query):
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

class GstreamerMessageBusProcess(threading.Thread):
    def __init__(self, core_queue, pipeline):
        super(GstreamerMessageBusProcess, self).__init__()
        self.core_queue = core_queue
        self.bus = pipeline.get_bus()

    def run(self):
        loop = gobject.MainLoop()
        gobject.threads_init()
        context = loop.get_context()
        while True:
            message = self.bus.pop_filtered(gst.MESSAGE_EOS)
            if message is not None:
                self.core_queue.put({'command': 'end_of_track'})
                logger.debug('Got and handled Gstreamer message of type: %s' % message.type)
            context.iteration(True)

class LibspotifySessionManager(SpotifySessionManager, threading.Thread):
    cache_location = os.path.expanduser(settings.SPOTIFY_LIB_CACHE)
    settings_location = os.path.expanduser(settings.SPOTIFY_LIB_CACHE)
    appkey_file = os.path.expanduser(settings.SPOTIFY_LIB_APPKEY)
    user_agent = 'Mopidy %s' % get_version()

    def __init__(self, username, password, core_queue, gstreamer_pipeline):
        SpotifySessionManager.__init__(self, username, password)
        threading.Thread.__init__(self)
        self.core_queue = core_queue
        self.connected = threading.Event()
        self.session = None
        self.gstreamer_pipeline = gstreamer_pipeline

        cap_string = """audio/x-raw-int,
                endianness=(int)1234,
                channels=(int)2,
                width=(int)16,
                depth=(int)16,
                signed=True,
                rate=(int)44100"""
        caps = gst.caps_from_string(cap_string)

        self.gsrc = gst.element_factory_make("appsrc", "app-source")
        self.gsrc.set_property('caps', caps)

        self.gsink = gst.element_factory_make("autoaudiosink", "autosink")

        self.gstreamer_pipeline.add(self.gsrc, self.gsink)

        gst.element_link_many(self.gsrc, self.gsink)

        message_process = GstreamerMessageBusProcess(self.core_queue, self.gstreamer_pipeline)
        message_process.start()

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
        cap_string = """audio/x-raw-int,
                endianness=(int)1234,
                channels=(int)2,
                width=(int)16,
                depth=(int)16,
                signed=True,
                rate=(int)44100"""
        caps = gst.caps_from_string(cap_string)
        b = gst.Buffer(frames)
        b.set_caps(caps)
        self.gsrc.emit('push-buffer', b)

    def play_token_lost(self, session):
        """Callback used by pyspotify"""
        logger.debug('Play token lost')
        self.core_queue.put({'command': 'stop_playback'})

    def log_message(self, session, data):
        """Callback used by pyspotify"""
        logger.debug(data)

    def end_of_track(self, session):
        """Callback used by pyspotify"""
        logger.debug('End of track.')
        self.gsrc.emit('end-of-stream')
        logger.debug('End of stream sent to gstreamer.')

    def search(self, query, connection):
        """Search method used by Mopidy backend"""
        def callback(results, userdata):
            logger.debug(u'In SessionManager.search().callback(), '
                'translating search results')
            logger.debug(results.tracks())
            # TODO Include results from results.albums(), etc. too
            playlist = Playlist(tracks=[
                LibspotifyTranslator.to_mopidy_track(t)
                for t in results.tracks()])
            logger.debug(u'In SessionManager.search().callback(), '
                'sending search results')
            logger.debug(['%s' % t.name for t in playlist.tracks])
            connection.send(playlist)
            logger.debug(u'In SessionManager.search().callback(), '
                'done sending search results')
        logger.debug(u'In SessionManager.search(), '
            'waiting for Spotify connection')
        self.connected.wait()
        logger.debug(u'In SessionManager.search(), '
            'sending search query')
        self.session.search(query, callback)
        logger.debug(u'In SessionManager.search(), '
            'done sending search query')
