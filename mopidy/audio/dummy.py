"""A dummy audio actor for use in tests.

This class implements the audio API in the simplest way possible. It is used in
tests of the core and backends.
"""

from __future__ import unicode_literals

import pykka

from .constants import PlaybackState
from .listener import AudioListener


class DummyAudio(pykka.ThreadingActor):
    def __init__(self):
        super(DummyAudio, self).__init__()
        self.state = PlaybackState.STOPPED
        self._position = 0

    def set_on_end_of_track(self, callback):
        pass

    def set_uri(self, uri):
        pass

    def set_appsrc(self, *args, **kwargs):
        pass

    def emit_data(self, buffer_):
        pass

    def emit_end_of_stream(self):
        pass

    def get_position(self):
        return self._position

    def set_position(self, position):
        self._position = position
        return True

    def start_playback(self):
        return self._change_state(PlaybackState.PLAYING)

    def pause_playback(self):
        return self._change_state(PlaybackState.PAUSED)

    def prepare_change(self):
        return True

    def stop_playback(self):
        return self._change_state(PlaybackState.STOPPED)

    def get_volume(self):
        return 0

    def set_volume(self, volume):
        pass

    def set_metadata(self, track):
        pass

    def _change_state(self, new_state):
        old_state, self.state = self.state, new_state
        AudioListener.send(
            'state_changed', old_state=old_state, new_state=new_state)
        return True
