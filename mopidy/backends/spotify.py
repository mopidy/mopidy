import logging
import sys

import spytify

from mopidy import settings
from mopidy.backends.base import BaseBackend

logger = logging.getLogger(u'spotify')

def encode(string):
    return string.encode('utf-8')

def decode(string):
    return string.decode('utf-8')

class SpotifyBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        super(SpotifyBackend, self).__init__(*args, **kwargs)
        logger.info(u'Connecting to Spotify')
        self.spotify = spytify.Spytify(self._username, self._password)
        logger.info(u'Preloading data')
        self._playlists
        logger.debug(u'Done preloading data')

    @property
    def _username(self):
        username = encode(settings.SPOTIFY_USERNAME)
        if not username:
            sys.exit(u'Setting SPOTIFY_USERNAME is not set.')
        return username

    @property
    def _password(self):
        password = encode(settings.SPOTIFY_PASSWORD)
        if not password:
            sys.exit(u'Setting SPOTIFY_PASSWORD is not set.')
        return password

    @property
    def _playlists(self):
        if not hasattr(self, '_x_playlists') or not self._x_playlists:
            logger.debug(u'Caching stored playlists')
            self._x_playlists = []
            for playlist in self.spotify.stored_playlists:
                self._x_playlists.append(playlist)
        return self._x_playlists

    @property
    def _current_playlist(self):
        if not hasattr(self, '_x_current_playlist'):
            self._x_current_playlist = []
        return self._x_current_playlist

    @_current_playlist.setter
    def _current_playlist(self, tracks):
        self._x_current_playlist = tracks
        self._x_current_playlist_version += 1

    @property
    def _current_playlist_version(self):
        if not hasattr(self, '_x_current_playlist_version'):
            self._x_current_playlist_version = 0
        return self._x_current_playlist_version

    ### MPD handlers

    def play_id(self, songid):
        track = self._current_playlist[songid]
        self.spotify.play(track)

    def playlist_load(self, name):
        playlists = filter(lambda p: decode(p.name) == name, self._playlists)
        if playlists:
            self._current_playlist = playlists[0].tracks
        else:
            self._current_playlist = []

    def playlists_list(self):
        return [u'playlist: %s' % decode(p.name) for p in self._playlists]

    def playlist_changes(self, songpos):
        tracks = []
        for i, track in enumerate(self._current_playlist):
            tracks.append(u'file: %s' % decode(track.track_id))
            tracks.append(u'Time: %d' % (track.length // 1000))
            tracks.append(u'Artist: %s' % decode(track.artists[0].name))
            tracks.append(u'Title: %s' % decode(track.title))
            tracks.append(u'Album: %s' % decode(track.album))
            tracks.append(u'Track: %s' % track.tracknumber)
            tracks.append(u'Pos: %d' % i)
            tracks.append(u'Id: %d' % i)
        return tracks

    def stop(self):
        self.spotify.stop()

    def status_playlist(self):
        return self._current_playlist_version

    def status_playlist_length(self):
        return len(self._current_playlist)

    def url_handlers(self):
        return [u'spotify:', u'http://open.spotify.com/']
