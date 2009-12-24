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

    def playlist_load(self, name):
        if not self._playlist_load_cache:
            for playlist in self.spotify.stored_playlists:
                if playlist.name == name:
                    tracks = []
                    for track in playlist.tracks:
                        tracks.append(u'add %s\n' % track.file_id)
                    self._playlist_load_cache = tracks
                    break
        return self._playlist_load_cache

    def playlists_list(self):
        playlists = []
        for playlist in self.spotify.stored_playlists:
            playlists.append(u'playlist: %s' % playlist.name.decode('utf-8'))
        return playlists


