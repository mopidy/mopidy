import logging

from spotify import Link, SpotifyError

from mopidy.backends.base import BasePlaybackController

logger = logging.getLogger('mopidy.backends.libspotify.playback')

class LibspotifyPlaybackController(BasePlaybackController):
    def _pause(self):
        return self.backend.output.set_state('PAUSED')

    def _play(self, track):
        self.backend.output.set_state('READY')
        if self.state == self.PLAYING:
            self.backend.spotify.session.play(0)
        if track.uri is None:
            return False
        try:
            self.backend.spotify.session.load(
                Link.from_string(track.uri).as_track())
            self.backend.spotify.session.play(1)
            self.backend.output.set_state('PLAYING')
            return True
        except SpotifyError as e:
            logger.warning('Play %s failed: %s', track.uri, e)
            return False

    def _resume(self):
        return self._seek(self.time_position)

    def _seek(self, time_position):
        self.backend.output.set_state('READY')
        self.backend.spotify.session.seek(time_position)
        self.backend.output.set_state('PLAYING')
        return True

    def _stop(self):
        result = self.backend.output.set_state('READY')
        self.backend.spotify.session.play(0)
        return result
