import logging
import time

from spotify import Link, SpotifyError

from mopidy.backends.base import BasePlaybackProvider
from mopidy.core import PlaybackState


logger = logging.getLogger('mopidy.backends.spotify.playback')


class SpotifyPlaybackProvider(BasePlaybackProvider):
    def __init__(self, *args, **kwargs):
        super(SpotifyPlaybackProvider, self).__init__(*args, **kwargs)

        self._timer = TrackPositionTimer()

    def pause(self):
        self._timer.pause()

        return super(SpotifyPlaybackProvider, self).pause()

    def play(self, track):
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

            self._timer.play()

            return True
        except SpotifyError as e:
            logger.info('Playback of %s failed: %s', track.uri, e)
            return False

    def resume(self):
        time_position = self.get_time_position()

        self._timer.resume()

        return self.seek(time_position)

    def seek(self, time_position):
        self.backend.audio.prepare_change()
        self.backend.spotify.session.seek(time_position)
        self.backend.audio.start_playback()

        self._timer.seek(time_position)

        return True

    def stop(self):
        self.backend.spotify.session.play(0)

        return super(SpotifyPlaybackProvider, self).stop()

    def get_time_position(self):
        # XXX: The default implementation of get_time_position hangs/times out
        # when used with the Spotify backend and GStreamer appsrc. If this can
        # be resolved, we no longer need to use a wall clock based time
        # position for Spotify playback.
        return self._timer.get_time_position()


class TrackPositionTimer(object):
    """
    Keeps track of time position in a track using the wall clock and playback
    events.

    To not introduce a reverse dependency on the playback controller, this
    class keeps track of playback state itself.
    """

    def __init__(self):
        self._state = PlaybackState.STOPPED
        self._accumulated = 0
        self._started = 0

    def play(self):
        self._state = PlaybackState.PLAYING
        self._accumulated = 0
        self._started = self._wall_time()

    def pause(self):
        self._state = PlaybackState.PAUSED
        self._accumulated += self._wall_time() - self._started

    def resume(self):
        self._state = PlaybackState.PLAYING

    def seek(self, time_position):
        self._started = self._wall_time()
        self._accumulated = time_position

    def get_time_position(self):
        if self._state == PlaybackState.PLAYING:
            time_since_started = self._wall_time() - self._started
            return self._accumulated + time_since_started
        elif self._state == PlaybackState.PAUSED:
            return self._accumulated
        elif self._state == PlaybackState.STOPPED:
            return 0

    def _wall_time(self):
        return int(time.time() * 1000)
