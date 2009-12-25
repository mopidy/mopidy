import spytify

from mopidy import settings
from mopidy.backends.base import BaseBackend

class SpotifyBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        super(SpotifyBackend, self).__init__(*args, **kwargs)
        self.spotify = spytify.Spytify(
            settings.SPOTIFY_USERNAME.encode('utf-8'),
            settings.SPOTIFY_PASSWORD.encode('utf-8'))
        self._playlist_load_cache = None
        self.current_playlist = []
        self.current_playlist_version = 0

    def playlist_load(self, name):
        for playlist in self.spotify.stored_playlists:
            if playlist.name == name:
                self.current_playlist = playlist.tracks
                self.current_playlist_version += len(playlist.tracks)
                break

    def playlists_list(self):
        if self._playlist_load_cache is None:
            self._playlist_load_cache = []
            for playlist in self.spotify.stored_playlists:
                self._playlist_load_cache.append(u'playlist: %s' % playlist.name.decode('utf-8'))
        return self._playlist_load_cache

    def status_playlist_length(self):
        return len(self.current_playlist)

    def playlist_changes(self, songpos):
        tracks = []
        pos = 0
        id = 0

        for track in self.current_playlist:
            tracks.append(u'file: %s' % track.track_id)
            tracks.append(u'Time: %d' % (track.length/1000))
            tracks.append(u'Artist: %s' % track.artists[0].name)
            tracks.append(u'Title: %s' % track.title)
            tracks.append(u'Album: %s' % track.album)
            tracks.append(u'Track: %s' % track.tracknumber)
            tracks.append(u'Pos: %d' % pos)
            tracks.append(u'Id: %d' % id)

            pos += 1
            id += 1
        return tracks

    def play_id(self, songid):
        track = self.current_playlist[songid]
        self.spotify.play(track)

    def stop(self):
        self.spotify.stop()

    def status_playlist(self):
        return self.current_playlist_version
