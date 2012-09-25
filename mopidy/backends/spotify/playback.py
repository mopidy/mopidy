import logging
import time

from spotify import Link, SpotifyError

from mopidy.backends.base import BasePlaybackProvider
from mopidy.core import PlaybackState


logger = logging.getLogger('mopidy.backends.spotify.playback')


class SpotifyPlaybackProvider(BasePlaybackProvider):
    def __init__(self, *args, **kwargs):
        super(SpotifyPlaybackProvider, self).__init__(*args, **kwargs)

        self._play_time_accumulated = 0
        self._play_time_started = 0

    def pause(self):
        time_since_started = self._wall_time() - self._play_time_started
        self._play_time_accumulated += time_since_started

        return super(SpotifyPlaybackProvider, self).pause()

    def play(self, track):
        if track.uri is None:
            return False

        self._play_time_accumulated = 0
        self._play_time_started = self._wall_time()

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
        self._play_time_started = self._wall_time()
        return self.seek(self.backend.playback.time_position)

    def seek(self, time_position):
        self._play_time_started = self._wall_time()
        self._play_time_accumulated = time_position

        self.backend.audio.prepare_change()
        self.backend.spotify.session.seek(time_position)
        self.backend.audio.start_playback()

        return True

    def stop(self):
        self.backend.spotify.session.play(0)
        return super(SpotifyPlaybackProvider, self).stop()

    def get_time_position(self):
        # XXX: The default implementation of get_time_position hangs/times out
        # when used with the Spotify backend and GStreamer appsrc. If this can
        # be resolved, we no longer need to use a wall clock based time
        # position for Spotify playback.
        state = self.backend.playback.state
        if state == PlaybackState.PLAYING:
            time_since_started = (self._wall_time() -
                self._play_time_started)
            return self._play_time_accumulated + time_since_started
        elif state == PlaybackState.PAUSED:
            return self._play_time_accumulated
        elif state == PlaybackState.STOPPED:
            return 0

    def _wall_time(self):
        return int(time.time() * 1000)
