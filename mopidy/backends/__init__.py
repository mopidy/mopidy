import logging
import random
import time

from mopidy.exceptions import MpdNotImplemented
from mopidy.models import Playlist

logger = logging.getLogger('backends.base')

class BaseBackend(object):
    current_playlist = None
    library = None
    playback = None
    stored_playlists = None
    uri_handlers = []

class BaseCurrentPlaylistController(object):
    def __init__(self, backend):
        self.backend = backend
        self.version = 0
        self.playlist = Playlist()

    def get_playlist(self):
        return self._playlist

    def set_playlist(self, playlist):
        self._playlist = playlist
        self.version += 1

    playlist = property(get_playlist, set_playlist)

    def add(self, uri, at_position=None):
        raise NotImplementedError

    def clear(self):
        self.backend.playback.stop()
        self.playlist = Playlist()

    def get_by_id(self, id):
        matches = filter(lambda t: t.id == id, self.playlist.tracks)
        if matches:
            return matches[0]
        else:
            raise KeyError('Track with ID "%s" not found' % id)

    def get_by_url(self, uri):
        matches = filter(lambda t: t.uri == uri, self.playlist.tracks)
        if matches:
            return matches[0]
        else:
            raise KeyError('Track with URI "%s" not found' % uri)

    def load(self, playlist):
        self.playlist = playlist

        playback = self.backend.playback

        # FIXME introduce a mechanism for telling
        # playback that it needs to reset
        playback.playlist_position = 0

        if playlist.tracks:
            playback.current_track = playlist.tracks[0]
        else:
            playback.current_track = None

        if playback.state == playback.PLAYING:
            self.backend.playback.play()

    def move(self, start, end, to_position):
        tracks = self.playlist.tracks

        if start == end:
            end += 1

        new_tracks = tracks[:start] + tracks[end:]

        for track in tracks[start:end]:
            new_tracks.insert(to_position, track)
            to_position += 1

        self.playlist = Playlist(tracks=new_tracks)

    def remove(self,track):
        tracks = filter(lambda t: t != track, self.playlist.tracks)

        self.playlist = Playlist(tracks=tracks)

    def shuffle(self, start=None, end=None):
        tracks = self.playlist.tracks

        before = tracks[:start or 0]
        shuffled = tracks[start:end]
        after = tracks[end or len(tracks):]

        random.shuffle(shuffled)

        self.playlist = Playlist(tracks=before+shuffled+after)

class BasePlaybackController(object):
    PAUSED = 'paused'
    PLAYING = 'playing'
    STOPPED = 'stopped'

    state = STOPPED
    
    def __init__(self, backend):
        self.backend = backend
        self.current_track = None
        self.playlist_position = 0

    def play(self, id=None, position=None):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def next(self):
        raise NotImplementedError

    @property
    def next_track(self):
        if self.current_track is None:
            return None
        try:
            return self.backend.current_playlist.playlist.tracks[
                self.playlist_position + 1]
        except IndexError:
            return None
