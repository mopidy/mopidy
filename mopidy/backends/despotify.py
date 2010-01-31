import datetime as dt
import logging
import sys

import spytify

from mopidy import config
from mopidy.backends import BaseBackend
from mopidy.models import Artist, Album, Track, Playlist

logger = logging.getLogger(u'backends.despotify')

ENCODING = 'utf-8'

class DespotifyBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        super(DespotifyBackend, self).__init__(*args, **kwargs)
        logger.info(u'Connecting to Spotify')
        self.spotify = spytify.Spytify(
            config.SPOTIFY_USERNAME, config.SPOTIFY_PASSWORD)
        self.cache_stored_playlists()

    def cache_stored_playlists(self):
        logger.info(u'Caching stored playlists')
        playlists = []
        for spotify_playlist in self.spotify.stored_playlists:
            playlists.append(self._to_mopidy_playlist(spotify_playlist))
        self._playlists = playlists
        logger.debug(u'Available playlists: %s',
            u', '.join([u'<%s>' % p.name for p in self._playlists]))

# Model translation

    def _to_mopidy_id(self, spotify_uri):
        return 0 # TODO

    def _to_mopidy_artist(self, spotify_artist):
        return Artist(
            uri=spotify_artist.get_uri(),
            name=spotify_artist.name.decode(ENCODING)
        )

    def _to_mopidy_album(self, spotify_album_name):
        return Album(name=spotify_album_name.decode(ENCODING))

    def _to_mopidy_track(self, spotify_track):
        if dt.MINYEAR <= int(spotify_track.year) <= dt.MAXYEAR:
            date = dt.date(spotify_track.year, 1, 1)
        else:
            date = None
        return Track(
            uri=spotify_track.get_uri(),
            title=spotify_track.title.decode(ENCODING),
            artists=[self._to_mopidy_artist(a) for a in spotify_track.artists],
            album=self._to_mopidy_album(spotify_track.album),
            track_no=spotify_track.tracknumber,
            date=date,
            length=spotify_track.length,
            id=self._to_mopidy_id(spotify_track.get_uri()),
        )

    def _to_mopidy_playlist(self, spotify_playlist):
        return Playlist(
            uri=spotify_playlist.get_uri(),
            name=spotify_playlist.name.decode(ENCODING),
            tracks=[self._to_mopidy_track(t) for t in spotify_playlist.tracks],
        )

# Play control

    def _next(self):
        self._current_song_pos += 1
        self.spotify.play(self.spotify.lookup(self._current_track.uri))
        return True

    def _pause(self):
        self.spotify.pause()
        return True

    def _play(self):
        if self._current_track is not None:
            self.spotify.play(self.spotify.lookup(self._current_track.uri))
            return True
        else:
            return False

    def _play_id(self, songid):
        self._current_song_pos = songid # XXX
        self.spotify.play(self.spotify.lookup(self._current_track.uri))
        return True

    def _play_pos(self, songpos):
        self._current_song_pos = songpos
        self.spotify.play(self.spotify.lookup(self._current_track.uri))
        return True

    def _previous(self):
        self._current_song_pos -= 1
        self.spotify.play(self.spotify.lookup(self._current_track.uri))
        return True

    def _resume(self):
        self.spotify.resume()
        return True

    def _stop(self):
        self.spotify.stop()
        return True

# Status querying

    def status_bitrate(self):
        return 320

    def url_handlers(self):
        return [u'spotify:', u'http://open.spotify.com/']

# Music database

    def search(self, type, what):
        query = u'%s:%s' % (type, what)
        result = self.spotify.search(query.encode(ENCODING))
        return self._to_mopidy_playlist(result.playlist).mpd_format()
