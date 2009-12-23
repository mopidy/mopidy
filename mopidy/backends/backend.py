
class BaseBackend(object):
    def current_song(self):
        return None

    def list_playlists(self):
        return None

    def playlist_changes(self, version):
        return None

    def status(self):
        return {
            'volume': 0,
            'repeat': 0,
            'random': 0,
            'single': 0,
            'consume': 0,
            'playlist': 0,
            'playlistlength': 0,
            'xfade': 0,
            'state': 'stop',
        }
