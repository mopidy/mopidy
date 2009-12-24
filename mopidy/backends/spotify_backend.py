import spytify

from mopidy import settings
from mopidy.backends.backend import BaseBackend

class SpotifyBackend(BaseBackend):
    def __init__(self, *args, **kwargs):
        super(SpotifyBackend, self).__init__(*args, **kwargs)
        self.spotify = spytify.Spytify(settings.SPOTIFY_USERNAME, settings.SPOTIFY_PASSWORD)

    def list_playlists(self):
        playlists = u''
        for playlist in self.spotify.stored_playlists:
            playlists += u'playlist: %s\n' % playlist.name
        return playlists

    def load(self, name):
        for playlist in self.spotify.stored_playlists:
            if playlist.name == 'name':
                break

        tracks = u''
        for track in playlist.tracks:
            tracks += u'add %s\n' % track.file_id
        return tracks
