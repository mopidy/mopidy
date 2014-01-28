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
        self._callback = None
        self._uri = None

    def set_uri(self, uri):
        assert self._uri is None, 'prepare change not called before set'
        self._uri = uri

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
        AudioListener.send('position_changed', position=position)
        return True

    def start_playback(self):
        return self._change_state(PlaybackState.PLAYING)

    def pause_playback(self):
        return self._change_state(PlaybackState.PAUSED)

    def prepare_change(self):
        self._uri = None
        return True

    def stop_playback(self):
        return self._change_state(PlaybackState.STOPPED)

    def get_volume(self):
        return 0

    def set_volume(self, volume):
        pass

    def set_metadata(self, track):
        pass

    def set_about_to_finish_callback(self, callback):
        self._callback = callback

    def _change_state(self, new_state):
        if not self._uri:
            return False

        if self.state == PlaybackState.STOPPED and self._uri:
            AudioListener.send('stream_changed', uri=self._uri)

        old_state, self.state = self.state, new_state
        AudioListener.send(
            'state_changed', old_state=old_state, new_state=new_state)

        return True

    def trigger_fake_end_of_stream(self):
        AudioListener.send('reached_end_of_stream')

    def trigger_fake_about_to_finish(self):
        if not self._callback:
            return
        self.prepare_change()
        self._callback()
        if not self._uri:
            self.trigger_fake_end_of_stream()
