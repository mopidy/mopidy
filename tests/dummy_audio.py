"""A dummy audio actor for use in tests.

This class implements the audio API in the simplest way possible. It is used in
tests of the core and backends.
"""

from typing import TYPE_CHECKING, cast, override

import pykka

from mopidy import audio
from mopidy.types import DurationMs, PlaybackState

if TYPE_CHECKING:
    from mopidy.internal.gi import Gst


def create_proxy(config=None, mixer=None):
    return DummyAudio.start(config, mixer).proxy()


# TODO: reset position on track change?
class DummyAudio(audio.Audio, pykka.ThreadingActor):
    def __init__(self, config=None, mixer=None):
        super().__init__()
        self.state = PlaybackState.STOPPED
        self._position = DurationMs(0)
        self._source_setup_callback = None
        self._about_to_finish_callback = None
        self._uri = None
        self._stream_changed = False
        self._live_stream = False
        self._tags = {}
        self._bad_uris = set()

    @override
    def set_uri(self, uri, live_stream=False, download=False):
        assert self._uri is None, "prepare change not called before set"
        self._position = DurationMs(0)
        self._uri = uri
        self._stream_changed = True
        self._live_stream = live_stream
        self._tags = {}

    @override
    def set_source_setup_callback(self, callback):
        self._source_setup_callback = callback

    @override
    def set_about_to_finish_callback(self, callback):
        self._about_to_finish_callback = callback

    @override
    def get_position(self):
        return self._position

    @override
    def set_position(self, position):
        self._position = position
        audio.AudioListener.send("position_changed", position=position)
        return True

    @override
    def start_playback(self):
        return self._change_state(PlaybackState.PLAYING)

    @override
    def pause_playback(self):
        return self._change_state(PlaybackState.PAUSED)

    @override
    def prepare_change(self):
        self._uri = None
        self._source_setup_callback = None
        return True

    @override
    def stop_playback(self):
        return self._change_state(PlaybackState.STOPPED)

    @override
    def get_current_tags(self):
        return self._tags

    def _change_state(self, new_state):
        if not self._uri:
            return False

        if new_state == PlaybackState.STOPPED and self._uri:
            self._stream_changed = True
            self._uri = None

        if self._stream_changed:
            self._stream_changed = False
            audio.AudioListener.send("stream_changed", uri=self._uri)

        if self._uri is not None:
            audio.AudioListener.send("position_changed", position=0)

        old_state, self.state = self.state, new_state
        audio.AudioListener.send(
            "state_changed",
            old_state=old_state,
            new_state=new_state,
            target_state=None,
        )

        if new_state == PlaybackState.PLAYING:
            self._tags["audio-codec"] = ["fake info..."]
            audio.AudioListener.send("tags_changed", tags=["audio-codec"])

        return self._uri not in self._bad_uris

    def trigger_fake_playback_failure(self, uri):
        self._bad_uris.add(uri)

    def trigger_fake_tags_changed(self, tags):
        self._tags.update(tags)
        audio.AudioListener.send("tags_changed", tags=self._tags.keys())

    def get_source_setup_callback(self):
        # This needs to be called from outside the actor or we lock up.
        def wrapper():
            if self._source_setup_callback:
                self._source_setup_callback(cast("Gst.Element", None))

        return wrapper

    def get_about_to_finish_callback(self):
        # This needs to be called from outside the actor or we lock up.
        def wrapper():
            if self._about_to_finish_callback:
                self.prepare_change()
                self._about_to_finish_callback()

            if not self._uri or not self._about_to_finish_callback:
                self._tags = {}
                audio.AudioListener.send("reached_end_of_stream")
            else:
                audio.AudioListener.send("position_changed", position=0)
                audio.AudioListener.send("stream_changed", uri=self._uri)

        return wrapper
