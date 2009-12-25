import sys

import spytify

from mopidy import settings
from mopidy.backends.base import BaseBackend

class SpotifyBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        super(SpotifyBackend, self).__init__(*args, **kwargs)
        self.spotify = spytify.Spytify(self.username, self.password)
        self._playlist_load_cache = None

    @property
    def username(self):
        username = settings.SPOTIFY_USERNAME.encode('utf-8')
        if not username:
            sys.exit('Setting SPOTIFY_USERNAME is not set.')
        return username

    @property
    def password(self):
        password = settings.SPOTIFY_PASSWORD.encode('utf-8')
        if not password:
            sys.exit('Setting SPOTIFY_PASSWORD is not set.')
        return password

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

    def url_handlers(self):
        return [u'spotify:', u'http://open.spotify.com/']
