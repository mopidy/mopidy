import logging

from spotify import Link, SpotifyError

from mopidy.backends.base import BasePlaybackProvider
from mopidy.core import PlaybackState

logger = logging.getLogger('mopidy.backends.spotify.playback')

class SpotifyPlaybackProvider(BasePlaybackProvider):
    def play(self, track):
        if self.backend.playback.state == PlaybackState.PLAYING:
            self.backend.spotify.session.play(0)
        if track.uri is None:
            return False
        try:
            self.backend.spotify.session.load(
                Link.from_string(track.uri).as_track())
            self.backend.spotify.session.play(1)
            self.backend.audio.prepare_change()
            self.backend.audio.set_uri('appsrc://')
            self.backend.audio.start_playback()
            self.backend.audio.set_metadata(track)
            return True
        except SpotifyError as e:
            logger.info('Playback of %s failed: %s', track.uri, e)
            return False

    def resume(self):
        return self.seek(self.backend.playback.time_position)

    def seek(self, time_position):
        self.backend.audio.prepare_change()
        self.backend.spotify.session.seek(time_position)
        self.backend.audio.start_playback()
        return True

    def stop(self):
        self.backend.spotify.session.play(0)
        return super(SpotifyPlaybackProvider, self).stop()
