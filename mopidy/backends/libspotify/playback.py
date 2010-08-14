import logging
import multiprocessing

from spotify import Link, SpotifyError

from mopidy.backends.base import BasePlaybackController
from mopidy.process import pickle_connection

logger = logging.getLogger('mopidy.backends.libspotify.playback')

class LibspotifyPlaybackController(BasePlaybackController):
    def _set_output_state(self, state_name):
        logger.debug(u'Setting output state to %s ...', state_name)
        (my_end, other_end) = multiprocessing.Pipe()
        self.backend.output_queue.put({
            'command': 'set_state',
            'state': state_name,
            'reply_to': pickle_connection(other_end),
        })
        my_end.poll(None)
        return my_end.recv()

    def _pause(self):
        return self._set_output_state('PAUSED')

    def _play(self, track):
        self._set_output_state('READY')
        if self.state == self.PLAYING:
            self.stop()
        if track.uri is None:
            return False
        try:
            self.backend.spotify.session.load(
                Link.from_string(track.uri).as_track())
            self.backend.spotify.session.play(1)
            self._set_output_state('PLAYING')
            return True
        except SpotifyError as e:
            logger.warning('Play %s failed: %s', track.uri, e)
            return False

    def _resume(self):
        return self._set_output_state('PLAYING')

    def _seek(self, time_position):
        self._set_output_state('READY')
        result = self.backend.spotify.session.seek(time_position)
        self._set_output_state('PLAYING')

    def _stop(self):
        result = self._set_output_state('READY')
        self.backend.spotify.session.play(0)
        return result
