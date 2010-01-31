import datetime as dt
import logging
import sys

import spytify

from mopidy import config
from mopidy.backends import BaseBackend
from mopidy.models import Artist, Album, Track, Playlist

logger = logging.getLogger(u'backends.despotify')

ENCODING = 'utf-8'

def to_mopidy_id(spotify_uri):
    return 0 # TODO

def to_mopidy_artist(spotify_artist):
    return Artist(
        uri=spotify_artist.get_uri(),
        name=spotify_artist.name.decode(ENCODING)
    )

def to_mopidy_album(spotify_album_name):
    return Album(name=spotify_album_name.decode(ENCODING))

def to_mopidy_track(spotify_track):
    if dt.MINYEAR <= int(spotify_track.year) <= dt.MAXYEAR:
        date = dt.date(spotify_track.year, 1, 1)
    else:
        date = None
    return Track(
        uri=spotify_track.get_uri(),
        title=spotify_track.title.decode(ENCODING),
        artists=[to_mopidy_artist(a) for a in spotify_track.artists],
        album=to_mopidy_album(spotify_track.album),
        track_no=spotify_track.tracknumber,
        date=date,
        length=spotify_track.length,
        id=to_mopidy_id(spotify_track.get_uri()),
    )

def to_mopidy_playlist(spotify_playlist):
    return Playlist(
        uri=spotify_playlist.get_uri(),
        name=spotify_playlist.name.decode(ENCODING),
        tracks=[to_mopidy_track(t) for t in spotify_playlist.tracks],
    )

class DespotifyBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        logger.info(u'Connecting to Spotify')
        self.spotify = spytify.Spytify(
            config.SPOTIFY_USERNAME, config.SPOTIFY_PASSWORD)
        self._playlists # Touch to cache

    def cache_stored_playlists(self):
        logger.info(u'Caching stored playlists')
        for spotify_playlist in self.spotify.stored_playlists:
            self._x_playlists.append(to_mopidy_playlist(spotify_playlist))

# State

    @property
    def _playlists(self):
        if not hasattr(self, '_x_playlists') or not self._x_playlists:
            self._x_playlists = []
        return self._x_playlists

    @property
    def _current_playlist(self):
        if not hasattr(self, '_x_current_playlist'):
            self._x_current_playlist = Playlist()
        return self._x_current_playlist

    @_current_playlist.setter
    def _current_playlist(self, playlist):
        self._x_current_playlist = playlist
        self._x_current_playlist_version += 1

    @property
    def _current_playlist_version(self):
        if not hasattr(self, '_x_current_playlist_version'):
            self._x_current_playlist_version = 0
        return self._x_current_playlist_version

    @property
    def _current_track(self):
        if self._current_song_pos is not None:
            return self._current_playlist.tracks[self._current_song_pos]

    @property
    def _current_song_pos(self):
        if not hasattr(self, '_x_current_song_pos'):
            self._x_current_song_pos = None
        if (self._current_playlist is None
                or self._current_playlist.length == 0):
            self._x_current_song_pos = None
        elif self._x_current_song_pos < 0:
            self._x_current_song_pos = 0
        elif self._x_current_song_pos >= self._current_playlist.length:
            self._x_current_song_pos = self._current_playlist.length - 1
        return self._x_current_song_pos

    @_current_song_pos.setter
    def _current_song_pos(self, songid):
        self._x_current_song_pos = songid

# Control methods

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

# Playlist methods

    def playlist_load(self, name):
        matches = filter(lambda p: p.name == name, self._playlists)
        if matches:
            self._current_playlist = matches[0]
        else:
            self._current_playlist = None

    def playlists_list(self):
        return [u'playlist: %s' % p.name for p in self._playlists]

    def playlist_changes_since(self, version='0'):
        if int(version) < self._current_playlist_version:
            return self._current_playlist.mpd_format()

    def playlist_info(self, songpos=None, start=0, end=None):
        if songpos is not None:
            start = int(songpos)
            end = start + 1
        return self._current_playlist.mpd_format(start, end)

# Status methods

    def current_song(self):
        if self.state is not self.STOP and self._current_track is not None:
            return self._current_track.mpd_format(self._current_song_pos)

    def status_bitrate(self):
        return 320

    def status_playlist(self):
        return self._current_playlist_version

    def status_playlist_length(self):
        return self._current_playlist.length

    def status_song_id(self):
        return self._current_song_pos # XXX

    def status_time_total(self):
        if self._current_track is not None:
            return self._current_track.length // 1000
        else:
            return 0

    def url_handlers(self):
        return [u'spotify:', u'http://open.spotify.com/']

# Music database methods

    def search(self, type, what):
        query = u'%s:%s' % (type, what)
        result = self.spotify.search(query.encode(ENCODING))
        return to_mopidy_playlist(result.playlist).mpd_format()
