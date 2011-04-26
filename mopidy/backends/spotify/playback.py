import logging

from spotify import Link, SpotifyError

from mopidy.backends.base import BasePlaybackProvider

logger = logging.getLogger('mopidy.backends.spotify.playback')

class SpotifyPlaybackProvider(BasePlaybackProvider):
    def pause(self):
        return self.backend.output.set_state('PAUSED')

    def play(self, track):
        self.backend.output.set_state('READY')
        if self.backend.playback.state == self.backend.playback.PLAYING:
            self.backend.spotify.session.play(0)
        if track.uri is None:
            return False
        try:
            self.backend.spotify.session.load(
                Link.from_string(track.uri).as_track())
            self.backend.spotify.session.play(1)
            self.backend.output.play_uri('appsrc://')
            return True
        except SpotifyError as e:
            logger.info('Playback of %s failed: %s', track.uri, e)
            return False

    def resume(self):
        return self.seek(self.backend.playback.time_position)

    def seek(self, time_position):
        self.backend.output.set_state('READY')
        self.backend.spotify.session.seek(time_position)
        self.backend.output.set_state('PLAYING')
        return True

    def stop(self):
        result = self.backend.output.set_state('READY')
        self.backend.spotify.session.play(0)
        return result
