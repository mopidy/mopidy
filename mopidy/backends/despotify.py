import datetime as dt
import logging
import sys

import spytify

from mopidy import settings
from mopidy.backends import (BaseBackend, BaseCurrentPlaylistController,
    BaseLibraryController, BasePlaybackController,
    BaseStoredPlaylistsController)
from mopidy.models import Artist, Album, Track, Playlist
from mopidy.utils import spotify_uri_to_int

logger = logging.getLogger('mopidy.backends.despotify')

ENCODING = 'utf-8'

class DespotifyBackend(BaseBackend):
    """
    A Spotify backend which uses the open source `despotify library
    <http://despotify.se/>`_.

    `spytify <http://despotify.svn.sourceforge.net/viewvc/despotify/src/bindings/python/>`_
    is the Python bindings for the despotify library. It got litle
    documentation, but a couple of examples are available.

    **Issues**

    - r503: Sometimes segfaults when traversing stored playlists, their tracks,
      artists, and albums. As it is not predictable, it may be a concurrency
      issue.

    - r503: Segfaults when looking up playlists, both your own lists and other
      peoples shared lists. To reproduce::

        >>> import spytify                                  # doctest: +SKIP
        >>> s = spytify.Spytify('alice', 'secret')          # doctest: +SKIP
        >>> s.lookup('spotify:user:klette:playlist:5rOGYPwwKqbAcVX8bW4k5V')
        ...                                                 # doctest: +SKIP
        Segmentation fault

    """

    def __init__(self, *args, **kwargs):
        super(DespotifyBackend, self).__init__(*args, **kwargs)
        self.current_playlist = DespotifyCurrentPlaylistController(backend=self)
        self.library = DespotifyLibraryController(backend=self)
        self.playback = DespotifyPlaybackController(backend=self)
        self.stored_playlists = DespotifyStoredPlaylistsController(backend=self)
        self.uri_handlers = [u'spotify:', u'http://open.spotify.com/']
        self.spotify = self._connect()
        self.stored_playlists.refresh()

    def _connect(self):
        logger.info(u'Connecting to Spotify')
        try:
            return DespotifySessionManager(
                settings.SPOTIFY_USERNAME.encode(ENCODING),
                settings.SPOTIFY_PASSWORD.encode(ENCODING),
                core_queue=self.core_queue)
        except spytify.SpytifyError as e:
            logger.exception(e)
            sys.exit(1)


class DespotifyCurrentPlaylistController(BaseCurrentPlaylistController):
    pass


class DespotifyLibraryController(BaseLibraryController):
    def lookup(self, uri):
        track = self.backend.spotify.lookup(uri.encode(ENCODING))
        return DespotifyTranslator.to_mopidy_track(track)

    def search(self, field, what):
        if field == u'track':
            field = u'title'
        if field == u'any':
            query = what
        else:
            query = u'%s:%s' % (field, what)
        result = self.backend.spotify.search(query.encode(ENCODING))
        if (result is None or result.playlist.tracks[0].get_uri() ==
                'spotify:track:0000000000000000000000'):
            return Playlist()
        return DespotifyTranslator.to_mopidy_playlist(result.playlist)

    find_exact = search


class DespotifyPlaybackController(BasePlaybackController):
    def _pause(self):
        self.backend.spotify.pause()
        return True

    def _play(self, track):
        self.backend.spotify.play(self.backend.spotify.lookup(track.uri))
        return True

    def _resume(self):
        self.backend.spotify.resume()
        return True

    def _stop(self):
        self.backend.spotify.stop()
        return True


class DespotifyStoredPlaylistsController(BaseStoredPlaylistsController):
    def refresh(self):
        logger.info(u'Caching stored playlists')
        playlists = []
        for spotify_playlist in self.backend.spotify.stored_playlists:
            playlists.append(
                DespotifyTranslator.to_mopidy_playlist(spotify_playlist))
        self._playlists = playlists
        logger.debug(u'Available playlists: %s',
            u', '.join([u'<%s>' % p.name for p in self.playlists]))
        logger.info(u'Done caching stored playlists')


class DespotifyTranslator(object):
    @classmethod
    def to_mopidy_id(cls, spotify_uri):
        return spotify_uri_to_int(spotify_uri)

    @classmethod
    def to_mopidy_artist(cls, spotify_artist):
        return Artist(
            uri=spotify_artist.get_uri(),
            name=spotify_artist.name.decode(ENCODING)
        )

    @classmethod
    def to_mopidy_album(cls, spotify_album_name):
        return Album(name=spotify_album_name.decode(ENCODING))

    @classmethod
    def to_mopidy_track(cls, spotify_track):
        if not spotify_track.has_meta_data():
            return None
        if dt.MINYEAR <= int(spotify_track.year) <= dt.MAXYEAR:
            date = dt.date(spotify_track.year, 1, 1)
        else:
            date = None
        return Track(
            uri=spotify_track.get_uri(),
            name=spotify_track.title.decode(ENCODING),
            artists=[cls.to_mopidy_artist(a) for a in spotify_track.artists],
            album=cls.to_mopidy_album(spotify_track.album),
            track_no=spotify_track.tracknumber,
            date=date,
            length=spotify_track.length,
            bitrate=320,
            id=cls.to_mopidy_id(spotify_track.get_uri()),
        )

    @classmethod
    def to_mopidy_playlist(cls, spotify_playlist):
        return Playlist(
            uri=spotify_playlist.get_uri(),
            name=spotify_playlist.name.decode(ENCODING),
            tracks=filter(None, [cls.to_mopidy_track(t) for t in spotify_playlist.tracks]),
        )


class DespotifySessionManager(spytify.Spytify):
    DESPOTIFY_NEW_TRACK = 1
    DESPOTIFY_TIME_TELL = 2
    DESPOTIFY_END_OF_PLAYLIST = 3
    DESPOTIFY_TRACK_PLAY_ERROR = 4

    def __init__(self, *args, **kwargs):
        kwargs['callback'] = self.callback
        self.core_queue = kwargs.pop('core_queue')
        super(DespotifySessionManager, self).__init__(*args, **kwargs)

    def callback(self, signal, data):
        if signal == self.DESPOTIFY_END_OF_PLAYLIST:
            logger.debug('Despotify signalled end of playlist')
            self.core_queue.put({'command': 'end_of_track'})
        elif signal == self.DESPOTIFY_TRACK_PLAY_ERROR:
            logger.error('Despotify signalled track play error')
