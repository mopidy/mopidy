class BaseBackend(object):
    PLAY = u'play'
    PAUSE = u'pause'
    STOP = u'stop'

    def __init__(self):
        self.state = self.STOP

    def current_song(self):
        return None

# Status methods
    def status_consume(self):
        return 0

    def status_volume(self):
        return 0

    def status_repeat(self):
        return 0

    def status_random(self):
        return 0

    def status_single(self):
        return 0

    def status_song_id(self):
        return 0

    def status_playlist(self):
        return 0

    def status_playlist_length(self):
        return 0

    def status_xfade(self):
        return 0

    def status_state(self):
        return self.state

# Control methods
    def next(self):
        pass

    def pause(self):
        self.state = self.PAUSE

    def play_pos(self, songpos):
        self.state = self.PLAY

    def play_id(self, songid):
        self.state = self.PLAY

    def previous(self):
        pass

    def resume(self):
        self.state = self.PLAY

    def stop(self):
        self.state = self.STOP

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
