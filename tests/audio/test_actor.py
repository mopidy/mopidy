from __future__ import absolute_import, unicode_literals

import threading
import unittest

import mock

import pykka

from mopidy import audio
from mopidy.audio.constants import PlaybackState
from mopidy.internal import path
from mopidy.internal.gi import Gst

from tests import dummy_audio, path_to_data_dir

# We want to make sure both our real audio class and the fake one behave
# correctly. So each test is first run against the real class, then repeated
# against our dummy.


class BaseTest(unittest.TestCase):
    config = {
        'audio': {
            'buffer_time': None,
            'mixer': 'fakemixer track_max_volume=65536',
            'mixer_track': None,
            'mixer_volume': None,
            'output': 'testoutput',
            'visualizer': None,
        }
    }

    uris = [path.path_to_uri(path_to_data_dir('song1.wav')),
            path.path_to_uri(path_to_data_dir('song2.wav'))]

    audio_class = audio.Audio

    def setUp(self):  # noqa: N802
        config = {
            'audio': {
                'buffer_time': None,
                'mixer': 'foomixer',
                'mixer_volume': None,
                'output': 'testoutput',
                'visualizer': None,
            },
            'proxy': {
                'hostname': '',
            },
        }
        self.song_uri = path.path_to_uri(path_to_data_dir('song1.wav'))
        self.audio = self.audio_class.start(config=config, mixer=None).proxy()

    def tearDown(self):  # noqa
        pykka.ActorRegistry.stop_all()

    def possibly_trigger_fake_playback_error(self, uri):
        pass

    def possibly_trigger_fake_about_to_finish(self):
        pass


class DummyMixin(object):
    audio_class = dummy_audio.DummyAudio

    def possibly_trigger_fake_playback_error(self, uri):
        self.audio.trigger_fake_playback_failure(uri)

    def possibly_trigger_fake_about_to_finish(self):
        callback = self.audio.get_about_to_finish_callback().get()
        if callback:
            callback()


class AudioTest(BaseTest):

    def test_start_playback_existing_file(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.assertTrue(self.audio.start_playback().get())

    def test_start_playback_non_existing_file(self):
        self.possibly_trigger_fake_playback_error(self.uris[0] + 'bogus')

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0] + 'bogus')
        self.assertFalse(self.audio.start_playback().get())

    def test_pause_playback_while_playing(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        self.assertTrue(self.audio.pause_playback().get())

    def test_stop_playback_while_playing(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        self.assertTrue(self.audio.stop_playback().get())

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
        super(DummyAudioListener, self).__init__()
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

    def setUp(self):  # noqa: N802
        super(AudioEventTest, self).setUp()
        self.audio.enable_sync_handler().get()
        self.listener = DummyAudioListener.start().proxy()

    def tearDown(self):  # noqa: N802
        super(AudioEventTest, self).tearDown()

    def assertEvent(self, event, **kwargs):  # noqa: N802
        self.assertIn((event, kwargs), self.listener.get_events().get())

    def assertNotEvent(self, event, **kwargs):  # noqa: N802
        self.assertNotIn((event, kwargs), self.listener.get_events().get())

    # TODO: test without uri set, with bad uri and gapless...
    # TODO: playing->playing triggered by seek should be removed
    # TODO: codify expected state after EOS
    # TODO: consider returning a future or a threading event?

    def test_state_change_stopped_to_playing_event(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        self.audio.wait_for_state_change().get()
        self.assertEvent('state_changed', old_state=PlaybackState.STOPPED,
                         new_state=PlaybackState.PLAYING, target_state=None)

    def test_state_change_stopped_to_paused_event(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()

        self.audio.wait_for_state_change().get()
        self.assertEvent('state_changed', old_state=PlaybackState.STOPPED,
                         new_state=PlaybackState.PAUSED, target_state=None)

    def test_state_change_paused_to_playing_event(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()

        self.audio.wait_for_state_change()
        self.listener.clear_events()
        self.audio.start_playback()

        self.audio.wait_for_state_change().get()
        self.assertEvent('state_changed', old_state=PlaybackState.PAUSED,
                         new_state=PlaybackState.PLAYING, target_state=None)

    def test_state_change_paused_to_stopped_event(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()

        self.audio.wait_for_state_change()
        self.listener.clear_events()
        self.audio.stop_playback()

        self.audio.wait_for_state_change().get()
        self.assertEvent('state_changed', old_state=PlaybackState.PAUSED,
                         new_state=PlaybackState.STOPPED, target_state=None)

    def test_state_change_playing_to_paused_event(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        self.audio.wait_for_state_change()
        self.listener.clear_events()
        self.audio.pause_playback()

        self.audio.wait_for_state_change().get()
        self.assertEvent('state_changed', old_state=PlaybackState.PLAYING,
                         new_state=PlaybackState.PAUSED, target_state=None)

    def test_state_change_playing_to_stopped_event(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        self.audio.wait_for_state_change()
        self.listener.clear_events()
        self.audio.stop_playback()

        self.audio.wait_for_state_change().get()
        self.assertEvent('state_changed', old_state=PlaybackState.PLAYING,
                         new_state=PlaybackState.STOPPED, target_state=None)

    def test_stream_changed_event_on_playing(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.listener.clear_events()
        self.audio.start_playback()

        # Since we are going from stopped to playing, the state change is
        # enough to ensure the stream changed.
        self.audio.wait_for_state_change().get()
        self.assertEvent('stream_changed', uri=self.uris[0])

    def test_stream_changed_event_on_multiple_changes(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.listener.clear_events()
        self.audio.start_playback()

        self.audio.wait_for_state_change().get()
        self.assertEvent('stream_changed', uri=self.uris[0])

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[1])
        self.audio.pause_playback()

        self.audio.wait_for_state_change().get()
        self.assertEvent('stream_changed', uri=self.uris[1])

    def test_stream_changed_event_on_playing_to_paused(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.listener.clear_events()
        self.audio.start_playback()

        self.audio.wait_for_state_change().get()
        self.assertEvent('stream_changed', uri=self.uris[0])

        self.listener.clear_events()
        self.audio.pause_playback()

        self.audio.wait_for_state_change().get()
        self.assertNotEvent('stream_changed', uri=self.uris[0])

    def test_stream_changed_event_on_paused_to_stopped(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()

        self.audio.wait_for_state_change()
        self.listener.clear_events()
        self.audio.stop_playback()

        self.audio.wait_for_state_change().get()
        self.assertEvent('stream_changed', uri=None)

    def test_position_changed_on_pause(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()
        self.audio.wait_for_state_change()

        self.audio.wait_for_state_change().get()
        self.assertEvent('position_changed', position=0)

    def test_stream_changed_event_on_paused_to_playing(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.listener.clear_events()
        self.audio.pause_playback()

        self.audio.wait_for_state_change().get()
        self.assertEvent('stream_changed', uri=self.uris[0])

        self.listener.clear_events()
        self.audio.start_playback()

        self.audio.wait_for_state_change().get()
        self.assertNotEvent('stream_changed', uri=self.uris[0])

    def test_position_changed_on_play(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        self.audio.wait_for_state_change()

        self.audio.wait_for_state_change().get()
        self.assertEvent('position_changed', position=0)

    def test_position_changed_on_seek_while_stopped(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.set_position(2000)

        self.audio.wait_for_state_change().get()
        self.assertNotEvent('position_changed', position=0)

    def test_position_changed_on_seek_after_play(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        self.audio.wait_for_state_change()
        self.listener.clear_events()
        self.audio.set_position(2000)

        self.audio.wait_for_state_change().get()
        self.assertEvent('position_changed', position=2000)

    def test_position_changed_on_seek_after_pause(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()

        self.audio.wait_for_state_change()
        self.listener.clear_events()
        self.audio.set_position(2000)

        self.audio.wait_for_state_change().get()
        self.assertEvent('position_changed', position=2000)

    def test_tags_changed_on_playback(self):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        self.audio.wait_for_state_change().get()

        self.assertEvent('tags_changed', tags=mock.ANY)

    # Unlike the other events, having the state changed done is not
    # enough to ensure our event is called. So we setup a threading
    # event that we can wait for with a timeout while the track playback
    # completes.

    def test_stream_changed_event_on_paused(self):
        event = self.listener.wait('stream_changed').get()

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback().get()
        self.audio.wait_for_state_change().get()

        if not event.wait(timeout=1.0):
            self.fail('Stream changed not reached within deadline')

        self.assertEvent('stream_changed', uri=self.uris[0])

    def test_reached_end_of_stream_event(self):
        event = self.listener.wait('reached_end_of_stream').get()

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        self.audio.wait_for_state_change().get()

        self.possibly_trigger_fake_about_to_finish()
        if not event.wait(timeout=1.0):
            self.fail('End of stream not reached within deadline')

        self.assertFalse(self.audio.get_current_tags().get())

    def test_gapless(self):
        uris = self.uris[1:]
        event = self.listener.wait('reached_end_of_stream').get()

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
            self.fail('EOS not received')

        # Check that both uris got played
        self.assertEvent('stream_changed', uri=self.uris[0])
        self.assertEvent('stream_changed', uri=self.uris[1])

        # Check that events counts check out.
        keys = [k for k, v in self.listener.get_events().get()]
        self.assertEqual(2, keys.count('stream_changed'))
        self.assertEqual(2, keys.count('position_changed'))
        self.assertEqual(1, keys.count('state_changed'))
        self.assertEqual(1, keys.count('reached_end_of_stream'))

        # TODO: test tag states within gaples

    # TODO: this does not belong in this testcase
    def test_current_tags_are_blank_to_begin_with(self):
        self.assertFalse(self.audio.get_current_tags().get())

    def test_current_tags_blank_after_end_of_stream(self):
        event = self.listener.wait('reached_end_of_stream').get()

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        self.possibly_trigger_fake_about_to_finish()
        self.audio.wait_for_state_change().get()

        if not event.wait(timeout=1.0):
            self.fail('EOS not received')

        self.assertFalse(self.audio.get_current_tags().get())

    def test_current_tags_stored(self):
        event = self.listener.wait('reached_end_of_stream').get()
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
            self.fail('EOS not received')

        self.assertTrue(tags[0])

    # TODO: test that we reset when we expect between songs


class AudioDummyEventTest(DummyMixin, AudioEventTest):

    """Exercise the AudioEventTest against our mock audio classes."""


# TODO: move to mixer tests...
class MixerTest(BaseTest):

    @unittest.SkipTest
    def test_set_mute(self):
        for value in (True, False):
            self.assertTrue(self.audio.set_mute(value).get())
            self.assertEqual(value, self.audio.get_mute().get())

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

    def setUp(self):  # noqa: N802
        self.audio = audio.Audio(config=None, mixer=None)

    def test_state_starts_as_stopped(self):
        self.assertEqual(audio.PlaybackState.STOPPED, self.audio.state)

    def test_state_does_not_change_when_in_gst_ready_state(self):
        self.audio._handler.on_playbin_state_changed(
            Gst.State.NULL, Gst.State.READY, Gst.State.VOID_PENDING)

        self.assertEqual(audio.PlaybackState.STOPPED, self.audio.state)

    def test_state_changes_from_stopped_to_playing_on_play(self):
        self.audio._handler.on_playbin_state_changed(
            Gst.State.NULL, Gst.State.READY, Gst.State.PLAYING)
        self.audio._handler.on_playbin_state_changed(
            Gst.State.READY, Gst.State.PAUSED, Gst.State.PLAYING)
        self.audio._handler.on_playbin_state_changed(
            Gst.State.PAUSED, Gst.State.PLAYING, Gst.State.VOID_PENDING)

        self.assertEqual(audio.PlaybackState.PLAYING, self.audio.state)

    def test_state_changes_from_playing_to_paused_on_pause(self):
        self.audio.state = audio.PlaybackState.PLAYING

        self.audio._handler.on_playbin_state_changed(
            Gst.State.PLAYING, Gst.State.PAUSED, Gst.State.VOID_PENDING)

        self.assertEqual(audio.PlaybackState.PAUSED, self.audio.state)

    def test_state_changes_from_playing_to_stopped_on_stop(self):
        self.audio.state = audio.PlaybackState.PLAYING

        self.audio._handler.on_playbin_state_changed(
            Gst.State.PLAYING, Gst.State.PAUSED, Gst.State.NULL)
        self.audio._handler.on_playbin_state_changed(
            Gst.State.PAUSED, Gst.State.READY, Gst.State.NULL)
        # We never get the following call, so the logic must work without it
        # self.audio._handler.on_playbin_state_changed(
        #     Gst.State.READY, Gst.State.NULL, Gst.State.VOID_PENDING)

        self.assertEqual(audio.PlaybackState.STOPPED, self.audio.state)


class AudioBufferingTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.audio = audio.Audio(config=None, mixer=None)
        self.audio._playbin = mock.Mock(spec=['set_state'])

    def test_pause_when_buffer_empty(self):
        playbin = self.audio._playbin
        self.audio.start_playback()
        playbin.set_state.assert_called_with(Gst.State.PLAYING)
        playbin.set_state.reset_mock()

        self.audio._handler.on_buffering(0)
        playbin.set_state.assert_called_with(Gst.State.PAUSED)
        self.assertTrue(self.audio._buffering)

    def test_stay_paused_when_buffering_finished(self):
        playbin = self.audio._playbin
        self.audio.pause_playback()
        playbin.set_state.assert_called_with(Gst.State.PAUSED)
        playbin.set_state.reset_mock()

        self.audio._handler.on_buffering(100)
        self.assertEqual(playbin.set_state.call_count, 0)
        self.assertFalse(self.audio._buffering)

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
        self.assertEqual(playbin.set_state.call_count, 0)
        self.assertFalse(self.audio._buffering)

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
        self.assertFalse(self.audio._buffering)
