import threading
import time
from typing import ClassVar
from unittest import mock

import pykka
import pytest

from mopidy import audio
from mopidy._lib import paths
from mopidy._lib.gi import Gst
from mopidy.audio._gst.pipeline import GstPipeline
from mopidy.types import PlaybackState
from tests import dummy_audio, path_to_data_dir

# We want to make sure both our real audio class and the fake one behave
# correctly. So each test is first run against the real class, then repeated
# against our dummy.


class BaseTest:
    uris: ClassVar[list[str]] = [
        paths.path_to_uri(path_to_data_dir("song1.wav")),
        paths.path_to_uri(path_to_data_dir("song2.wav")),
    ]

    audio_class = audio.GstAudio

    def setup_method(self):
        config = {
            "audio": {
                "buffer_time": None,
                "mixer": "foomixer",
                "mixer_volume": None,
                "output": "testoutput",
                "visualizer": None,
            },
            "proxy": {"hostname": ""},
        }
        self.song_uri = paths.path_to_uri(path_to_data_dir("song1.wav"))
        self.audio = self.audio_class.start(config=config, mixer=None).proxy()

    def teardown_method(self):
        pykka.ActorRegistry.stop_all()

    def possibly_trigger_fake_playback_error(self, uri):
        pass

    def possibly_trigger_fake_about_to_finish(self):
        pass

    def possibly_trigger_fake_source_setup(self):
        pass


class DummyMixin:
    audio_class = dummy_audio.DummyAudio
    audio: pykka.ActorProxy[dummy_audio.DummyAudio]

    def possibly_trigger_fake_playback_error(self, uri):
        self.audio.trigger_fake_playback_failure(uri)

    def possibly_trigger_fake_about_to_finish(self):
        callback = self.audio.get_about_to_finish_callback().get()
        if callback:
            callback()

    def possibly_trigger_fake_source_setup(self):
        callback = self.audio.get_source_setup_callback().get()
        if callback:
            callback()


class TestAudio(BaseTest):
    def test_start_playback_existing_file(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        assert self.audio.start_playback().get()

    def test_start_playback_non_existing_file(self):
        self.possibly_trigger_fake_playback_error(self.uris[0] + "bogus")

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0] + "bogus")
        assert not self.audio.start_playback().get()

    def test_pause_playback_while_playing(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        assert self.audio.pause_playback().get()

    def test_stop_playback_while_playing(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        assert self.audio.stop_playback().get()

    @pytest.mark.skip(reason="Not implemented")
    def test_deliver_data(self):
        pass  # TODO: Implement test

    @pytest.mark.skip(reason="Not implemented")
    def test_end_of_data_stream(self):
        pass  # TODO: Implement test

    @pytest.mark.skip(reason="Not implemented")
    def test_set_mute(self):
        pass  # TODO: Implement test

    @pytest.mark.skip(reason="Not implemented")
    def test_set_state_encapsulation(self):
        pass  # TODO: Implement test

    @pytest.mark.skip(reason="Not implemented")
    def test_set_position(self):
        pass  # TODO: Implement test

    @pytest.mark.skip(reason="Not implemented")
    def test_invalid_output_raises_error(self):
        pass  # TODO: Implement test


class TestAudioDummy(DummyMixin, TestAudio):
    pass


class DummyAudioListener(pykka.ThreadingActor, audio.AudioListener):
    def __init__(self):
        super().__init__()
        self.events = []
        self.waiters = {}

    def on_event(self, event, **kwargs):
        self.events.append((event, kwargs))
        if event in self.waiters:
            self.waiters[event].set()

    def wait(self, event):
        self.waiters[event] = threading.Event()
        return self.waiters[event]

    def get_events(self):
        return self.events

    def clear_events(self):
        self.events = []


class TestAudioEvent(BaseTest):
    def setup_method(self):
        super().setup_method()
        self.listener = DummyAudioListener.start().proxy()

    def assert_event(self, event, **kwargs):
        # Bus messages reach the listener through two actors now, so the
        # event can arrive shortly after the state change completes.
        deadline = time.monotonic() + 1.0
        while (event, kwargs) not in self.listener.get_events().get():
            if time.monotonic() > deadline:
                msg = f"Event {event!r} with {kwargs!r} never arrived"
                raise AssertionError(msg)
            time.sleep(0.005)

    def assert_not_event(self, event, **kwargs):
        assert (event, kwargs) not in self.listener.get_events().get()

    # TODO: test without uri set, with bad uri and gapless...
    # TODO: playing->playing triggered by seek should be removed
    # TODO: codify expected state after EOS
    # TODO: consider returning a future or a threading event?

    def test_state_change_stopped_to_playing_event(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_event(
            "state_changed",
            old_state=PlaybackState.STOPPED,
            new_state=PlaybackState.PLAYING,
            target_state=None,
        )

    def test_state_change_stopped_to_paused_event(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_event(
            "state_changed",
            old_state=PlaybackState.STOPPED,
            new_state=PlaybackState.PAUSED,
            target_state=None,
        )

    def test_state_change_paused_to_playing_event(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()

        self.audio.testing_gst__wait_for_state_change()
        self.listener.clear_events()
        self.audio.start_playback()

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_event(
            "state_changed",
            old_state=PlaybackState.PAUSED,
            new_state=PlaybackState.PLAYING,
            target_state=None,
        )

    def test_state_change_paused_to_stopped_event(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()

        self.audio.testing_gst__wait_for_state_change()
        self.listener.clear_events()
        self.audio.stop_playback()

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_event(
            "state_changed",
            old_state=PlaybackState.PAUSED,
            new_state=PlaybackState.STOPPED,
            target_state=None,
        )

    def test_state_change_playing_to_paused_event(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        self.audio.testing_gst__wait_for_state_change()
        self.listener.clear_events()
        self.audio.pause_playback()

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_event(
            "state_changed",
            old_state=PlaybackState.PLAYING,
            new_state=PlaybackState.PAUSED,
            target_state=None,
        )

    def test_state_change_playing_to_stopped_event(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        self.audio.testing_gst__wait_for_state_change()
        self.listener.clear_events()
        self.audio.stop_playback()

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_event(
            "state_changed",
            old_state=PlaybackState.PLAYING,
            new_state=PlaybackState.STOPPED,
            target_state=None,
        )

    def test_stream_changed_event_on_playing(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.listener.clear_events()
        self.audio.start_playback()

        # Since we are going from stopped to playing, the state change is
        # enough to ensure the stream changed.
        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_event("stream_changed", uri=self.uris[0])

    def test_stream_changed_event_on_multiple_changes(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.listener.clear_events()
        self.audio.start_playback()

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_event("stream_changed", uri=self.uris[0])

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[1])
        self.audio.pause_playback()

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_event("stream_changed", uri=self.uris[1])

    def test_stream_changed_event_on_playing_to_paused(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.listener.clear_events()
        self.audio.start_playback()

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_event("stream_changed", uri=self.uris[0])

        self.listener.clear_events()
        self.audio.pause_playback()

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_not_event("stream_changed", uri=self.uris[0])

    def test_stream_changed_event_on_paused_to_stopped(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()

        self.audio.testing_gst__wait_for_state_change()
        self.listener.clear_events()
        self.audio.stop_playback()

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_event("stream_changed", uri=None)

    def test_position_changed_on_pause(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()
        self.audio.testing_gst__wait_for_state_change()

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_event("position_changed", position=0)

    def test_stream_changed_event_on_paused_to_playing(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.listener.clear_events()
        self.audio.pause_playback()

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_event("stream_changed", uri=self.uris[0])

        self.listener.clear_events()
        self.audio.start_playback()

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_not_event("stream_changed", uri=self.uris[0])

    def test_position_changed_on_play(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        self.audio.testing_gst__wait_for_state_change()

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_event("position_changed", position=0)

    def test_position_changed_on_seek_while_stopped(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.set_position(2000)

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_not_event("position_changed", position=0)

    def test_position_changed_on_seek_after_play(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        self.audio.testing_gst__wait_for_state_change()
        self.listener.clear_events()
        self.audio.set_position(2000)

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_event("position_changed", position=2000)

    def test_position_changed_on_seek_after_pause(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()

        self.audio.testing_gst__wait_for_state_change()
        self.listener.clear_events()
        self.audio.set_position(2000)

        self.audio.testing_gst__wait_for_state_change().get()
        self.assert_event("position_changed", position=2000)

    def test_tags_changed_on_playback(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        self.audio.testing_gst__wait_for_state_change().get()

        self.assert_event("tags_changed", tags=mock.ANY)

    # Unlike the other events, having the state changed done is not
    # enough to ensure our event is called. So we setup a threading
    # event that we can wait for with a timeout while the track playback
    # completes.

    def test_stream_changed_event_on_paused(self):
        event = self.listener.wait("stream_changed").get()

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback().get()
        self.audio.testing_gst__wait_for_state_change().get()

        if not event.wait(timeout=1.0):
            pytest.fail("Stream changed not reached within deadline")

        self.assert_event("stream_changed", uri=self.uris[0])

    def test_reached_end_of_stream_event(self):
        event = self.listener.wait("reached_end_of_stream").get()

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        self.audio.testing_gst__wait_for_state_change().get()

        self.possibly_trigger_fake_about_to_finish()
        if not event.wait(timeout=1.0):
            pytest.fail("End of stream not reached within deadline")

        assert not self.audio.get_current_tags().get()

    def test_gapless(self):
        uris = self.uris[1:]
        event = self.listener.wait("reached_end_of_stream").get()

        def callback():
            if uris:
                self.audio.set_uri(uris.pop()).get()

        self.audio.set_about_to_finish_callback(callback).get()

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        self.possibly_trigger_fake_about_to_finish()
        self.audio.testing_gst__wait_for_state_change().get()

        self.possibly_trigger_fake_about_to_finish()
        self.audio.testing_gst__wait_for_state_change().get()
        if not event.wait(timeout=1.0):
            pytest.fail("EOS not received")

        # Check that both uris got played
        self.assert_event("stream_changed", uri=self.uris[0])
        self.assert_event("stream_changed", uri=self.uris[1])

        # Check that events counts check out.
        keys = [k for k, v in self.listener.get_events().get()]
        assert keys.count("stream_changed") == 2
        assert keys.count("position_changed") == 2
        assert keys.count("state_changed") == 1
        assert keys.count("reached_end_of_stream") == 1

        # TODO: test tag states within gaples

    def test_source_setup(self):
        mock_callback = mock.Mock()

        self.audio.prepare_change()
        self.audio.set_source_setup_callback(mock_callback).get()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        self.possibly_trigger_fake_source_setup()
        self.audio.testing_gst__wait_for_state_change().get()

        mock_callback.assert_called_once()

    # TODO: this does not belong in this testcase
    def test_current_tags_are_blank_to_begin_with(self):
        assert not self.audio.get_current_tags().get()

    def test_current_tags_blank_after_end_of_stream(self):
        event = self.listener.wait("reached_end_of_stream").get()

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        self.possibly_trigger_fake_about_to_finish()
        self.audio.testing_gst__wait_for_state_change().get()

        if not event.wait(timeout=1.0):
            pytest.fail("EOS not received")

        assert not self.audio.get_current_tags().get()

    def test_current_tags_stored(self):
        event = self.listener.wait("reached_end_of_stream").get()
        tags = []

        def callback():
            tags.append(self.audio.get_current_tags().get())

        self.audio.set_about_to_finish_callback(callback).get()

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        self.possibly_trigger_fake_about_to_finish()
        self.audio.testing_gst__wait_for_state_change().get()

        if not event.wait(timeout=1.0):
            pytest.fail("EOS not received")

        assert tags[0]

    # TODO: test that we reset when we expect between songs


class TestAudioDummyEvent(DummyMixin, TestAudioEvent):
    """Exercise the TestAudioEvent against our mock audio classes."""


@pytest.fixture
def gst_audio():
    # Not started as an actor, so there is no real playbin.
    return audio.GstAudio(config={"proxy": {}}, mixer=None)


@pytest.fixture
def pipeline(gst_audio):
    # The pipeline owns the elements, so inject a fake one.
    gst_audio._pipeline = mock.Mock(spec=GstPipeline)
    return gst_audio._pipeline


@pytest.fixture
def source():
    source = mock.MagicMock()
    source.props = mock.Mock(spec=["is_live"])
    return source


def test_state_starts_as_stopped(gst_audio):
    assert gst_audio.state == PlaybackState.STOPPED


def test_state_does_not_change_when_in_gst_ready_state(gst_audio):
    gst_audio._on_gst_state_changed(
        Gst.State.NULL,
        Gst.State.READY,
        Gst.State.VOID_PENDING,
    )

    assert gst_audio.state == PlaybackState.STOPPED


def test_state_changes_from_stopped_to_playing_on_play(gst_audio):
    gst_audio._on_gst_state_changed(
        Gst.State.NULL,
        Gst.State.READY,
        Gst.State.PLAYING,
    )
    gst_audio._on_gst_state_changed(
        Gst.State.READY,
        Gst.State.PAUSED,
        Gst.State.PLAYING,
    )
    gst_audio._on_gst_state_changed(
        Gst.State.PAUSED,
        Gst.State.PLAYING,
        Gst.State.VOID_PENDING,
    )

    assert gst_audio.state == PlaybackState.PLAYING


def test_state_changes_from_playing_to_paused_on_pause(gst_audio):
    gst_audio.state = PlaybackState.PLAYING

    gst_audio._on_gst_state_changed(
        Gst.State.PLAYING,
        Gst.State.PAUSED,
        Gst.State.VOID_PENDING,
    )

    assert gst_audio.state == PlaybackState.PAUSED


def test_state_changes_from_playing_to_stopped_on_stop(gst_audio):
    gst_audio.state = PlaybackState.PLAYING

    gst_audio._on_gst_state_changed(
        Gst.State.PLAYING,
        Gst.State.PAUSED,
        Gst.State.NULL,
    )
    gst_audio._on_gst_state_changed(
        Gst.State.PAUSED,
        Gst.State.READY,
        Gst.State.NULL,
    )
    # We never get the following call, so the logic must work without it
    # gst_audio._on_gst_state_changed(
    #     Gst.State.READY, Gst.State.NULL, Gst.State.VOID_PENDING)

    assert gst_audio.state == PlaybackState.STOPPED


def test_buffering_pause_when_buffer_empty(gst_audio, pipeline):
    gst_audio.start_playback()
    pipeline.set_state.assert_called_with(Gst.State.PLAYING)
    pipeline.set_state.reset_mock()

    gst_audio._on_gst_buffering(0, Gst.BufferingMode.STREAM)
    pipeline.set_state.assert_called_with(Gst.State.PAUSED)
    assert gst_audio._buffering


def test_buffering_stay_paused_when_buffering_finished(gst_audio, pipeline):
    gst_audio.pause_playback()
    pipeline.set_state.assert_called_with(Gst.State.PAUSED)
    pipeline.set_state.reset_mock()

    gst_audio._on_gst_buffering(100, Gst.BufferingMode.STREAM)
    assert pipeline.set_state.call_count == 0
    assert not gst_audio._buffering


def test_buffering_change_to_paused_while_buffering(gst_audio, pipeline):
    gst_audio.start_playback()
    pipeline.set_state.assert_called_with(Gst.State.PLAYING)
    pipeline.set_state.reset_mock()

    gst_audio._on_gst_buffering(0, Gst.BufferingMode.STREAM)
    pipeline.set_state.assert_called_with(Gst.State.PAUSED)
    gst_audio.pause_playback()
    pipeline.set_state.reset_mock()

    gst_audio._on_gst_buffering(100, Gst.BufferingMode.STREAM)
    assert pipeline.set_state.call_count == 0
    assert not gst_audio._buffering


def test_buffering_change_to_stopped_while_buffering(gst_audio, pipeline):
    gst_audio.start_playback()
    pipeline.set_state.assert_called_with(Gst.State.PLAYING)
    pipeline.set_state.reset_mock()

    gst_audio._on_gst_buffering(0, Gst.BufferingMode.STREAM)
    pipeline.set_state.assert_called_with(Gst.State.PAUSED)
    pipeline.set_state.reset_mock()

    gst_audio.stop_playback()
    pipeline.set_state.assert_called_with(Gst.State.NULL)
    assert not gst_audio._buffering


def test_source_setup_not_live_mode(gst_audio, source):
    gst_audio._live_stream = False

    gst_audio._on_gst_source_setup("dummy", source)

    source.set_live.assert_not_called()


def test_source_setup_live_mode(gst_audio, source):
    gst_audio._live_stream = True

    gst_audio._on_gst_source_setup("dummy", source)

    source.set_live.assert_called_with(True)


def test_source_setup_callback(gst_audio, source):
    mock_callback = mock.MagicMock()
    gst_audio.set_source_setup_callback(mock_callback)

    gst_audio._on_gst_source_setup("dummy", source)

    mock_callback.assert_called_once_with(source)

    gst_audio.set_source_setup_callback(None)

    gst_audio._on_gst_source_setup("dummy", source)

    mock_callback.assert_called_once()
