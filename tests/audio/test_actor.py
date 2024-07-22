import threading
import unittest
from typing import ClassVar
from unittest import mock

import pykka
from mopidy import audio
from mopidy.internal import path
from mopidy.internal.gi import Gst
from mopidy.types import PlaybackState

from tests import dummy_audio, path_to_data_dir

# We want to make sure both our real audio class and the fake one behave
# correctly. So each test is first run against the real class, then repeated
# against our dummy.


class BaseTest(unittest.TestCase):
    uris: ClassVar[list[str]] = [
        path.path_to_uri(path_to_data_dir("song1.wav")),
        path.path_to_uri(path_to_data_dir("song2.wav")),
    ]

    audio_class = audio.Audio

    def setUp(self):
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
        self.song_uri = path.path_to_uri(path_to_data_dir("song1.wav"))
        self.audio = self.audio_class.start(config=config, mixer=None).proxy()

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def possibly_trigger_fake_playback_error(self, uri):
        pass

    def possibly_trigger_fake_about_to_finish(self):
        pass

    def possibly_trigger_fake_source_setup(self):
        pass


class DummyMixin:
    audio_class = dummy_audio.DummyAudio

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


class AudioTest(BaseTest):
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

    @unittest.SkipTest
    def test_deliver_data(self):
        pass  # TODO

    @unittest.SkipTest
    def test_end_of_data_stream(self):
        pass  # TODO

    @unittest.SkipTest
    def test_set_mute(self):
        pass  # TODO Probably needs a fakemixer with a mixer track

    @unittest.SkipTest
    def test_set_state_encapsulation(self):
        pass  # TODO

    @unittest.SkipTest
    def test_set_position(self):
        pass  # TODO

    @unittest.SkipTest
    def test_invalid_output_raises_error(self):
        pass  # TODO


class AudioDummyTest(DummyMixin, AudioTest):
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


class AudioEventTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.audio.enable_sync_handler().get()
        self.listener = DummyAudioListener.start().proxy()

    def tearDown(self):
        super().tearDown()

    def assert_event(self, event, **kwargs):
        assert (event, kwargs) in self.listener.get_events().get()

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

        self.audio.wait_for_state_change().get()
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

        self.audio.wait_for_state_change().get()
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

        self.audio.wait_for_state_change()
        self.listener.clear_events()
        self.audio.start_playback()

        self.audio.wait_for_state_change().get()
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

        self.audio.wait_for_state_change()
        self.listener.clear_events()
        self.audio.stop_playback()

        self.audio.wait_for_state_change().get()
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

        self.audio.wait_for_state_change()
        self.listener.clear_events()
        self.audio.pause_playback()

        self.audio.wait_for_state_change().get()
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

        self.audio.wait_for_state_change()
        self.listener.clear_events()
        self.audio.stop_playback()

        self.audio.wait_for_state_change().get()
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
        self.audio.wait_for_state_change().get()
        self.assert_event("stream_changed", uri=self.uris[0])

    def test_stream_changed_event_on_multiple_changes(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.listener.clear_events()
        self.audio.start_playback()

        self.audio.wait_for_state_change().get()
        self.assert_event("stream_changed", uri=self.uris[0])

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[1])
        self.audio.pause_playback()

        self.audio.wait_for_state_change().get()
        self.assert_event("stream_changed", uri=self.uris[1])

    def test_stream_changed_event_on_playing_to_paused(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.listener.clear_events()
        self.audio.start_playback()

        self.audio.wait_for_state_change().get()
        self.assert_event("stream_changed", uri=self.uris[0])

        self.listener.clear_events()
        self.audio.pause_playback()

        self.audio.wait_for_state_change().get()
        self.assert_not_event("stream_changed", uri=self.uris[0])

    def test_stream_changed_event_on_paused_to_stopped(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()

        self.audio.wait_for_state_change()
        self.listener.clear_events()
        self.audio.stop_playback()

        self.audio.wait_for_state_change().get()
        self.assert_event("stream_changed", uri=None)

    def test_position_changed_on_pause(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()
        self.audio.wait_for_state_change()

        self.audio.wait_for_state_change().get()
        self.assert_event("position_changed", position=0)

    def test_stream_changed_event_on_paused_to_playing(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.listener.clear_events()
        self.audio.pause_playback()

        self.audio.wait_for_state_change().get()
        self.assert_event("stream_changed", uri=self.uris[0])

        self.listener.clear_events()
        self.audio.start_playback()

        self.audio.wait_for_state_change().get()
        self.assert_not_event("stream_changed", uri=self.uris[0])

    def test_position_changed_on_play(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        self.audio.wait_for_state_change()

        self.audio.wait_for_state_change().get()
        self.assert_event("position_changed", position=0)

    def test_position_changed_on_seek_while_stopped(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.set_position(2000)

        self.audio.wait_for_state_change().get()
        self.assert_not_event("position_changed", position=0)

    def test_position_changed_on_seek_after_play(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        self.audio.wait_for_state_change()
        self.listener.clear_events()
        self.audio.set_position(2000)

        self.audio.wait_for_state_change().get()
        self.assert_event("position_changed", position=2000)

    def test_position_changed_on_seek_after_pause(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()

        self.audio.wait_for_state_change()
        self.listener.clear_events()
        self.audio.set_position(2000)

        self.audio.wait_for_state_change().get()
        self.assert_event("position_changed", position=2000)

    def test_tags_changed_on_playback(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        self.audio.wait_for_state_change().get()

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
        self.audio.wait_for_state_change().get()

        if not event.wait(timeout=1.0):
            self.fail("Stream changed not reached within deadline")

        self.assert_event("stream_changed", uri=self.uris[0])

    def test_reached_end_of_stream_event(self):
        event = self.listener.wait("reached_end_of_stream").get()

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        self.audio.wait_for_state_change().get()

        self.possibly_trigger_fake_about_to_finish()
        if not event.wait(timeout=1.0):
            self.fail("End of stream not reached within deadline")

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
        self.audio.wait_for_state_change().get()

        self.possibly_trigger_fake_about_to_finish()
        self.audio.wait_for_state_change().get()
        if not event.wait(timeout=1.0):
            self.fail("EOS not received")

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
        self.audio.wait_for_state_change().get()

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
        self.audio.wait_for_state_change().get()

        if not event.wait(timeout=1.0):
            self.fail("EOS not received")

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
        self.audio.wait_for_state_change().get()

        if not event.wait(timeout=1.0):
            self.fail("EOS not received")

        assert tags[0]

    # TODO: test that we reset when we expect between songs


class AudioDummyEventTest(DummyMixin, AudioEventTest):
    """Exercise the AudioEventTest against our mock audio classes."""


# TODO: move to mixer tests...
class MixerTest(BaseTest):
    @unittest.SkipTest
    def test_set_mute(self):
        for value in (True, False):
            assert self.audio.set_mute(value).get()
            assert self.audio.get_mute().get() == value

    @unittest.SkipTest
    def test_set_state_encapsulation(self):
        pass  # TODO

    @unittest.SkipTest
    def test_set_position(self):
        pass  # TODO

    @unittest.SkipTest
    def test_invalid_output_raises_error(self):
        pass  # TODO


class AudioStateTest(unittest.TestCase):
    def setUp(self):
        self.audio = audio.Audio(config=None, mixer=None)

    def test_state_starts_as_stopped(self):
        assert self.audio.state == audio.PlaybackState.STOPPED

    def test_state_does_not_change_when_in_gst_ready_state(self):
        self.audio._handler.on_playbin_state_changed(
            Gst.State.NULL, Gst.State.READY, Gst.State.VOID_PENDING
        )

        assert self.audio.state == audio.PlaybackState.STOPPED

    def test_state_changes_from_stopped_to_playing_on_play(self):
        self.audio._handler.on_playbin_state_changed(
            Gst.State.NULL, Gst.State.READY, Gst.State.PLAYING
        )
        self.audio._handler.on_playbin_state_changed(
            Gst.State.READY, Gst.State.PAUSED, Gst.State.PLAYING
        )
        self.audio._handler.on_playbin_state_changed(
            Gst.State.PAUSED, Gst.State.PLAYING, Gst.State.VOID_PENDING
        )

        assert self.audio.state == audio.PlaybackState.PLAYING

    def test_state_changes_from_playing_to_paused_on_pause(self):
        self.audio.state = audio.PlaybackState.PLAYING

        self.audio._handler.on_playbin_state_changed(
            Gst.State.PLAYING, Gst.State.PAUSED, Gst.State.VOID_PENDING
        )

        assert self.audio.state == audio.PlaybackState.PAUSED

    def test_state_changes_from_playing_to_stopped_on_stop(self):
        self.audio.state = audio.PlaybackState.PLAYING

        self.audio._handler.on_playbin_state_changed(
            Gst.State.PLAYING, Gst.State.PAUSED, Gst.State.NULL
        )
        self.audio._handler.on_playbin_state_changed(
            Gst.State.PAUSED, Gst.State.READY, Gst.State.NULL
        )
        # We never get the following call, so the logic must work without it
        # self.audio._handler.on_playbin_state_changed(
        #     Gst.State.READY, Gst.State.NULL, Gst.State.VOID_PENDING)

        assert self.audio.state == audio.PlaybackState.STOPPED


class AudioBufferingTest(unittest.TestCase):
    def setUp(self):
        self.audio = audio.Audio(config=None, mixer=None)
        self.audio._playbin = mock.Mock(spec=["set_state"])

    def test_pause_when_buffer_empty(self):
        playbin = self.audio._playbin
        self.audio.start_playback()
        playbin.set_state.assert_called_with(Gst.State.PLAYING)
        playbin.set_state.reset_mock()

        self.audio._handler.on_buffering(0)
        playbin.set_state.assert_called_with(Gst.State.PAUSED)
        assert self.audio._buffering

    def test_stay_paused_when_buffering_finished(self):
        playbin = self.audio._playbin
        self.audio.pause_playback()
        playbin.set_state.assert_called_with(Gst.State.PAUSED)
        playbin.set_state.reset_mock()

        self.audio._handler.on_buffering(100)
        assert playbin.set_state.call_count == 0
        assert not self.audio._buffering

    def test_change_to_paused_while_buffering(self):
        playbin = self.audio._playbin
        self.audio.start_playback()
        playbin.set_state.assert_called_with(Gst.State.PLAYING)
        playbin.set_state.reset_mock()

        self.audio._handler.on_buffering(0)
        playbin.set_state.assert_called_with(Gst.State.PAUSED)
        self.audio.pause_playback()
        playbin.set_state.reset_mock()

        self.audio._handler.on_buffering(100)
        assert playbin.set_state.call_count == 0
        assert not self.audio._buffering

    def test_change_to_stopped_while_buffering(self):
        playbin = self.audio._playbin
        self.audio.start_playback()
        playbin.set_state.assert_called_with(Gst.State.PLAYING)
        playbin.set_state.reset_mock()

        self.audio._handler.on_buffering(0)
        playbin.set_state.assert_called_with(Gst.State.PAUSED)
        playbin.set_state.reset_mock()

        self.audio.stop_playback()
        playbin.set_state.assert_called_with(Gst.State.NULL)
        assert not self.audio._buffering


class AudioLiveTest(unittest.TestCase):
    def setUp(self):
        config = {"proxy": {}}
        self.audio = audio.Audio(config=config, mixer=None)
        self.audio._playbin = mock.Mock(spec=["set_property"])

        self.source = mock.MagicMock()
        self.source.props = mock.Mock(spec=["is_live"])

    def test_not_live_mode(self):
        self.audio._live_stream = False

        self.audio._on_source_setup("dummy", self.source)

        self.source.set_live.assert_not_called()

    def test_live_mode(self):
        self.audio._live_stream = True

        self.audio._on_source_setup("dummy", self.source)

        self.source.set_live.assert_called_with(True)


class DownloadBufferingTest(unittest.TestCase):
    def setUp(self):
        self.audio = audio.Audio(config=None, mixer=None)
        self.audio._playbin = mock.Mock(spec=["set_property"])

    def test_download_flag_is_passed_to_playbin_if_download_buffering_is_enabled(
        self,
    ):
        playbin = self.audio._playbin

        self.audio.set_uri("some:uri", False, True)

        playbin.set_property.assert_has_calls([mock.call("flags", 0x02 | 0x80)])

    def test_download_flag_is_not_passed_to_playbin_if_download_buffering_is_disabled(
        self,
    ):
        playbin = self.audio._playbin

        self.audio.set_uri("some:uri", False, False)

        playbin.set_property.assert_has_calls([mock.call("flags", 0x02)])


class SourceSetupCallbackTest(unittest.TestCase):
    def setUp(self):
        config = {"proxy": {}}
        self.audio = audio.Audio(config=config, mixer=None)
        self.audio._playbin = mock.Mock(spec=["set_property"])

        self.source = mock.MagicMock()

    def test_source_setup_callback(self):
        mock_callback = mock.MagicMock()
        self.audio.set_source_setup_callback(mock_callback)

        self.audio._on_source_setup("dummy", self.source)

        mock_callback.assert_called_once_with(self.source)

        self.audio.set_source_setup_callback(None)

        self.audio._on_source_setup("dummy", self.source)

        mock_callback.assert_called_once()
