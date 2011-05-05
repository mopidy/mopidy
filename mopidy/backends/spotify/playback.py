import logging

from spotify import Link, SpotifyError

from mopidy.backends.base import BasePlaybackProvider

logger = logging.getLogger('mopidy.backends.spotify.playback')

class SpotifyPlaybackProvider(BasePlaybackProvider):
    def pause(self):
        return self.backend.gstreamer.pause_playback()

    def play(self, track):
        if self.backend.playback.state == self.backend.playback.PLAYING:
            self.backend.spotify.session.play(0)
        if track.uri is None:
            return False
        try:
            self.backend.spotify.session.load(
                Link.from_string(track.uri).as_track())
            self.backend.spotify.session.play(1)
            self.backend.gstreamer.prepare_change()
            self.backend.gstreamer.set_uri('appsrc://')
            self.backend.gstreamer.start_playback()
            self.backend.gstreamer.set_metadata(track)
            return True
        except SpotifyError as e:
            logger.info('Playback of %s failed: %s', track.uri, e)
            return False

    def resume(self):
        return self.seek(self.backend.playback.time_position)

    def seek(self, time_position):
        self.backend.gstreamer.prepare_change()
        self.backend.spotify.session.seek(time_position)
        self.backend.gstreamer.start_playback()
        return True

    def stop(self):
        result = self.backend.gstreamer.stop_playback()
        self.backend.spotify.session.play(0)
        return result
