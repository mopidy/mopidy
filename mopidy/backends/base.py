
class BaseBackend(object):
    def current_song(self):
        return None

# Status methods
    def status_volume(self):
        return 0

    def status_repeat(self):
        return 0

    def status_random(self):
        return 0

    def status_single(self):
        return 0

    def status_consume(self):
        return 0

    def status_playlist(self):
        return 0

    def status_playlist_length(self):
        return 0

    def status_xfade(self):
        return 0

    def status_state(self):
        return 'stop'

# Control methods
    def stop(self):
        pass

    def play(self, songid):
        pass

    def play_id(self, songid):
        pass

# Current/single playlist methods
    def playlist_changes_since(self, version):
        return None

    def playlist_load(self, name):
        pass

    def playlist_info(self, songpos, start, end):
        return None

# Stored playlist methods
    def playlists_list(self):
        return None
