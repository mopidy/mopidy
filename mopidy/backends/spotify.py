import logging
import sys

import spytify

from mopidy import settings
from mopidy.backends.base import BaseBackend

logger = logging.getLogger(u'backends.spotify')

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

    def _format_playlist(self, playlist, pos_range=None):
        if pos_range is None:
            pos_range = range(len(playlist))
        tracks = []
        for track, pos in zip(playlist, pos_range):
            tracks.extend(self._format_track(track, pos))
        return tracks

    def _format_track(self, track, pos=0):
        result = []
        result.append(u'file: %s' % track.get_uri())
        result.append(u'Time: %d' % (track.length // 1000))
        result.append(u'Artist: %s' % self._format_artists(track.artists))
        result.append(u'Title: %s' % decode(track.title))
        result.append(u'Album: %s' % decode(track.album))
        result.append(u'Track: %d/0' % track.tracknumber)
        result.append(u'Date: %s' % track.year)
        result.append(u'Pos: %d' % pos)
        result.append(u'Id: %d' % pos)
        return result

    def _format_artists(self, artists):
        artist_names = [decode(artist.name) for artist in artists]
        return u', '.join(artist_names)


    ### MPD handlers

    def current_song(self):
        track = self.spotify.current_track
        if track is not None and self.state in (self.PLAY, self.PAUSE):
            return self._format_track(track)

    def play_id(self, songid):
        self.state = self.PLAY
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

    def playlist_info(self, songpos=None, start=None, end=None):
        if songpos is not None:
            songpos = int(songpos)
            return self._format_track(self._current_playlist[songpos], songpos)
        elif start is not None:
            start = int(start)
            if end is not None:
                end = int(end)
                return self._format_playlist(self._current_playlist[start:end],
                    range(start, end))
            else:
                return self._format_playlist(self._current_playlist[start:],
                    range(start, len(self._current_playlist)))
        else:
            return self._format_playlist(self._current_playlist)

    def playlist_changes_since(self, version='0'):
        if int(version) < self._current_playlist_version:
            return self._format_playlist(self._current_playlist)

    def stop(self):
        self.state = self.STOP
        self.spotify.stop()

    def status_playlist(self):
        return self._current_playlist_version

    def status_playlist_length(self):
        return len(self._current_playlist)

    def url_handlers(self):
        return [u'spotify:', u'http://open.spotify.com/']
