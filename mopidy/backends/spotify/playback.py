import logging

from spotify import Link, SpotifyError

from mopidy.backends.base import BasePlaybackProvider

logger = logging.getLogger('mopidy.backends.spotify.playback')

class SpotifyPlaybackProvider(BasePlaybackProvider):
    def pause(self):
        return self.backend.audio.pause_playback()

    def play(self, track):
        if self.backend.playback.state == self.backend.playback.PLAYING:
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
        result = self.backend.audio.stop_playback()
        self.backend.spotify.session.play(0)
        return result

    def get_volume(self):
        return self.backend.audio.get_volume().get()

    def set_volume(self, volume):
        self.backend.audio.set_volume(volume)
