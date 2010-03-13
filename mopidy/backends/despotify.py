import datetime as dt
import logging

import spytify

from mopidy import settings
from mopidy.backends import (BaseBackend, BaseCurrentPlaylistController,
    BaseLibraryController, BasePlaybackController,
    BaseStoredPlaylistsController)
from mopidy.models import Artist, Album, Track, Playlist

logger = logging.getLogger(u'backends.despotify')

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

        >>> import spytify
        >>> s = spytify.Spytify('alice', 'secret')
        >>> s.lookup('spotify:user:klette:playlist:5rOGYPwwKqbAcVX8bW4k5V')
        Segmentation fault

    """

    def __init__(self, *args, **kwargs):
        super(DespotifyBackend, self).__init__(*args, **kwargs)
        self.current_playlist = DespotifyCurrentPlaylistController(backend=self)
        self.library = DespotifyLibraryController(backend=self)
        self.playback = DespotifyPlaybackController(backend=self)
        self.stored_playlists = DespotifyStoredPlaylistsController(backend=self)
        self.uri_handlers = [u'spotify:', u'http://open.spotify.com/']
        self.translate = DespotifyTranslator()
        self.spotify = self._connect()
        self.stored_playlists.refresh()

    def _connect(self):
        logger.info(u'Connecting to Spotify')
        return spytify.Spytify(
            settings.SPOTIFY_USERNAME.encode(ENCODING),
            settings.SPOTIFY_PASSWORD.encode(ENCODING))


class DespotifyCurrentPlaylistController(BaseCurrentPlaylistController):
    pass


class DespotifyLibraryController(BaseLibraryController):
    def lookup(self, uri):
        track = self.backend.spotify.lookup(uri.encode(ENCODING))
        return self.backend.translate.to_mopidy_track(track)

    def search(self, type, what):
        if type == u'track':
            type = u'title'
        if type == u'any':
            query = what
        else:
            query = u'%s:%s' % (type, what)
        result = self.backend.spotify.search(query.encode(ENCODING))
        if (result is None or result.playlist.tracks[0].get_uri() ==
                'spotify:track:0000000000000000000000'):
            return Playlist()
        return self.backend.translate.to_mopidy_playlist(result.playlist)

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
                self.backend.translate.to_mopidy_playlist(spotify_playlist))
        self._playlists = playlists
        logger.debug(u'Available playlists: %s',
            u', '.join([u'<%s>' % p.name for p in self.playlists]))


class DespotifyTranslator(object):
    uri_to_id_map = {}
    next_id = 0

    def to_mopidy_id(self, spotify_uri):
        if spotify_uri not in self.uri_to_id_map:
            this_id = self.next_id
            self.next_id += 1
            self.uri_to_id_map[spotify_uri] = this_id
        return self.uri_to_id_map[spotify_uri]

    def to_mopidy_artist(self, spotify_artist):
        return Artist(
            uri=spotify_artist.get_uri(),
            name=spotify_artist.name.decode(ENCODING)
        )

    def to_mopidy_album(self, spotify_album_name):
        return Album(name=spotify_album_name.decode(ENCODING))

    def to_mopidy_track(self, spotify_track):
        if dt.MINYEAR <= int(spotify_track.year) <= dt.MAXYEAR:
            date = dt.date(spotify_track.year, 1, 1)
        else:
            date = None
        return Track(
            uri=spotify_track.get_uri(),
            name=spotify_track.title.decode(ENCODING),
            artists=[self.to_mopidy_artist(a) for a in spotify_track.artists],
            album=self.to_mopidy_album(spotify_track.album),
            track_no=spotify_track.tracknumber,
            date=date,
            length=spotify_track.length,
            bitrate=320,
            id=self.to_mopidy_id(spotify_track.get_uri()),
        )

    def to_mopidy_playlist(self, spotify_playlist):
        return Playlist(
            uri=spotify_playlist.get_uri(),
            name=spotify_playlist.name.decode(ENCODING),
            tracks=[self.to_mopidy_track(t) for t in spotify_playlist.tracks],
        )
