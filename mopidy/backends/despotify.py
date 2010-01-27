import logging
import sys

import spytify

from mopidy import config
from mopidy.backends.base import BaseBackend

logger = logging.getLogger(u'backends.despotify')

def encode(string):
    return string.encode('utf-8')

def decode(string):
    return string.decode('utf-8')

class DespotifyBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        logger.info(u'Connecting to Spotify')
        self.spotify = spytify.Spytify(
            config.SPOTIFY_USERNAME, config.SPOTIFY_PASSWORD)
        logger.info(u'Preloading data')
        self._playlists
        logger.debug(u'Done preloading data')

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

    @property
    def _current_track(self):
        if self._current_song_pos is not None:
            return self._current_playlist[self._current_song_pos]

    @property
    def _current_song_pos(self):
        if not hasattr(self, '_x_current_song_pos'):
            self._x_current_song_pos = None
        if self._current_playlist is None or len(self._current_playlist) == 0:
            self._x_current_song_pos = None
        elif self._x_current_song_pos < 0:
            self._x_current_song_pos = 0
        elif self._x_current_song_pos >= len(self._current_playlist):
            self._x_current_song_pos = len(self._current_playlist) - 1
        return self._x_current_song_pos

    @_current_song_pos.setter
    def _current_song_pos(self, songid):
        self._x_current_song_pos = songid

    def _format_playlist(self, playlist, pos_range=None):
        if pos_range is None:
            pos_range = range(len(playlist))
        tracks = []
        for track, pos in zip(playlist, pos_range):
            tracks.append(self._format_track(track, pos))
        return tracks

    def _format_track(self, track, pos=0):
        result = [
            ('file', track.get_uri()),
            ('Time', (track.length // 1000)),
            ('Artist', self._format_artists(track.artists)),
            ('Title', decode(track.title)),
            ('Album', decode(track.album)),
            ('Track', '%d/0' % track.tracknumber),
            ('Date', track.year),
            ('Pos', pos),
            ('Id', pos),
        ]
        return result

    def _format_artists(self, artists):
        artist_names = [decode(artist.name) for artist in artists]
        return u', '.join(artist_names)

# Control methods

    def _next(self):
        self._current_song_pos += 1
        self.spotify.play(self._current_track)
        return True

    def _pause(self):
        self.spotify.pause()
        return True

    def _play(self):
        if self._current_track is not None:
            self.spotify.play(self._current_track)
            return True
        else:
            return False

    def _play_id(self, songid):
        self._current_song_pos = songid # XXX
        self.spotify.play(self._current_track)
        return True

    def _play_pos(self, songpos):
        self._current_song_pos = songpos
        self.spotify.play(self._current_track)
        return True

    def _previous(self):
        self._current_song_pos -= 1
        self.spotify.play(self._current_track)
        return True

    def _resume(self):
        self.spotify.resume()
        return True

    def _stop(self):
        self.spotify.stop()
        return True

# Playlist methods

    def playlist_load(self, name):
        playlists = filter(lambda p: decode(p.name) == name, self._playlists)
        if playlists:
            self._current_playlist = playlists[0].tracks
        else:
            self._current_playlist = []

    def playlists_list(self):
        return [u'playlist: %s' % decode(p.name) for p in self._playlists]

    def playlist_changes_since(self, version='0'):
        if int(version) < self._current_playlist_version:
            return self._format_playlist(self._current_playlist)

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

# Status methods

    def current_song(self):
        if self.state is not self.STOP and self._current_track is not None:
            return self._format_track(self._current_track,
                self._current_song_pos)

    def status_bitrate(self):
        return 320

    def status_playlist(self):
        return self._current_playlist_version

    def status_playlist_length(self):
        return len(self._current_playlist)

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
        result = self.spotify.search(encode(u'%s:%s' % (type, what)))
        return self._format_playlist(result.playlist.tracks)
