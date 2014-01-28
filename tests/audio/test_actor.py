from __future__ import unicode_literals

import mock
import threading
import unittest

import pygst
pygst.require('0.10')
import gst

import gobject
gobject.threads_init()

import pykka

from mopidy import audio
from mopidy.audio import dummy as dummy_audio
from mopidy.audio.constants import PlaybackState
from mopidy.utils.path import path_to_uri

from tests import path_to_data_dir

"""
We want to make sure both our real audio class and the fake one behave
correctly. So each test is first run against the real class, then repeated
against our dummy.
"""


class BaseTest(unittest.TestCase):
    config = {
        'audio': {
            'mixer': 'fakemixer track_max_volume=65536',
            'mixer_track': None,
            'mixer_volume': None,
            'output': 'fakesink',
            'visualizer': None,
        }
    }

    uris = [path_to_uri(path_to_data_dir('song1.wav')),
            path_to_uri(path_to_data_dir('song2.wav'))]

    audio_class = audio.Audio

    def setUp(self):
        self.audio = self.audio_class.start(config=self.config).proxy()

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def possibly_trigger_fake_playback_error(self):
        pass

    def possibly_trigger_fake_about_to_finish(self):
        pass


class DummyMixin(object):
    audio_class = dummy_audio.DummyAudio

    def possibly_trigger_fake_playback_error(self):
        self.audio.trigger_fake_playback_failure()

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
        self.possibly_trigger_fake_playback_error()

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


@mock.patch.object(audio.AudioListener, 'send')
class AudioEventTest(BaseTest):
    def setUp(self):
        super(AudioEventTest, self).setUp()
        self.audio.enable_sync_handler().get()

    # TODO: test wihtout uri set, with bad uri and gapless...
    # TODO: playing->playing triggered by seek should be removed

    def test_state_change_stopped_to_playing_event(self, send_mock):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        self.audio.wait_for_state_change().get()
        call = mock.call('state_changed', old_state=PlaybackState.STOPPED,
                         new_state=PlaybackState.PLAYING)
        self.assertIn(call, send_mock.call_args_list)

    def test_state_change_stopped_to_paused_event(self, send_mock):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()

        self.audio.wait_for_state_change().get()
        call = mock.call('state_changed', old_state=PlaybackState.STOPPED,
                         new_state=PlaybackState.PAUSED)
        self.assertIn(call, send_mock.call_args_list)

    def test_state_change_paused_to_playing_event(self, send_mock):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()
        self.audio.wait_for_state_change()
        self.audio.start_playback()

        self.audio.wait_for_state_change().get()
        call = mock.call('state_changed', old_state=PlaybackState.PAUSED,
                         new_state=PlaybackState.PLAYING)
        self.assertIn(call, send_mock.call_args_list)

    def test_state_change_paused_to_stopped_event(self, send_mock):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()
        self.audio.wait_for_state_change()
        self.audio.stop_playback()

        self.audio.wait_for_state_change().get()
        call = mock.call('state_changed', old_state=PlaybackState.PAUSED,
                         new_state=PlaybackState.STOPPED)
        self.assertIn(call, send_mock.call_args_list)

    def test_state_change_playing_to_paused_event(self, send_mock):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        self.audio.wait_for_state_change()
        self.audio.pause_playback()

        self.audio.wait_for_state_change().get()
        call = mock.call('state_changed', old_state=PlaybackState.PLAYING,
                         new_state=PlaybackState.PAUSED)
        self.assertIn(call, send_mock.call_args_list)

    def test_state_change_playing_to_stopped_event(self, send_mock):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        self.audio.wait_for_state_change()
        self.audio.stop_playback()

        self.audio.wait_for_state_change().get()
        call = mock.call('state_changed', old_state=PlaybackState.PLAYING,
                         new_state=PlaybackState.STOPPED)
        self.assertIn(call, send_mock.call_args_list)

    def test_stream_changed_event_on_playing(self, send_mock):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        # Since we are going from stopped to playing, the state change is
        # enough to ensure the stream changed.
        self.audio.wait_for_state_change().get()

        call = mock.call('stream_changed', uri=self.uris[0])
        self.assertIn(call, send_mock.call_args_list)

    def test_stream_changed_event_on_paused_to_stopped(self, send_mock):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()
        self.audio.wait_for_state_change()
        self.audio.stop_playback()

        self.audio.wait_for_state_change().get()

        call = mock.call('stream_changed', uri=None)
        self.assertIn(call, send_mock.call_args_list)

    def test_position_changed_on_pause(self, send_mock):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()
        self.audio.wait_for_state_change()

        self.audio.wait_for_state_change().get()

        call = mock.call('position_changed', position=0)
        self.assertIn(call, send_mock.call_args_list)

    def test_position_changed_on_play(self, send_mock):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        self.audio.wait_for_state_change()

        self.audio.wait_for_state_change().get()

        call = mock.call('position_changed', position=0)
        self.assertIn(call, send_mock.call_args_list)

    def test_position_changed_on_seek(self, send_mock):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.set_position(2000)

        self.audio.wait_for_state_change().get()

        call = mock.call('position_changed', position=0)
        self.assertNotIn(call, send_mock.call_args_list)

    def test_position_changed_on_seek_after_play(self, send_mock):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        self.audio.wait_for_state_change()
        self.audio.set_position(2000)

        self.audio.wait_for_state_change().get()

        call = mock.call('position_changed', position=2000)
        self.assertIn(call, send_mock.call_args_list)

    def test_position_changed_on_seek_after_pause(self, send_mock):
        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback()
        self.audio.wait_for_state_change()
        self.audio.set_position(2000)

        self.audio.wait_for_state_change().get()

        call = mock.call('position_changed', position=2000)
        self.assertIn(call, send_mock.call_args_list)

    # Unlike the other events, having the state changed done is not
    # enough to ensure our event is called. So we setup a threading
    # event that we can wait for with a timeout while the track playback
    # completes.

    def test_stream_changed_event_on_paused(self, send_mock):
        event = threading.Event()

        def send(name, **kwargs):
            if name == 'stream_changed':
                event.set()
        send_mock.side_effect = send

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.pause_playback().get()
        self.audio.wait_for_state_change().get()

        if not event.wait(timeout=1.0):
            self.fail('Stream changed not reached within deadline')

    def test_reached_end_of_stream_event(self, send_mock):
        event = threading.Event()

        def send(name, **kwargs):
            if name == 'reached_end_of_stream':
                event.set()
        send_mock.side_effect = send

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()
        self.audio.wait_for_state_change().get()

        self.possibly_trigger_fake_about_to_finish()
        if not event.wait(timeout=1.0):
            self.fail('End of stream not reached within deadline')

    # Make sure that gapless really works:

    def test_gapless(self, send_mock):
        uris = self.uris[1:]
        events = []
        done = threading.Event()

        def callback():
            if uris:
                self.audio.set_uri(uris.pop()).get()

        def send(name, **kwargs):
            events.append((name, kwargs))
            if name == 'reached_end_of_stream':
                done.set()

        send_mock.side_effect = send
        self.audio.set_about_to_finish_callback(callback).get()

        self.audio.prepare_change()
        self.audio.set_uri(self.uris[0])
        self.audio.start_playback()

        self.possibly_trigger_fake_about_to_finish()
        self.audio.wait_for_state_change().get()

        self.possibly_trigger_fake_about_to_finish()
        if not done.wait(timeout=1.0):
            self.fail('EOS not received')

        excepted = [
            ('position_changed', {'position': 0}),
            ('stream_changed', {'uri': self.uris[0]}),
            ('state_changed', {'old_state': PlaybackState.STOPPED,
                               'new_state': PlaybackState.PLAYING}),
            ('position_changed', {'position': 0}),
            ('stream_changed', {'uri': self.uris[1]}),
            ('reached_end_of_stream', {})]
        self.assertEqual(excepted, events)


class AudioDummyEventTest(DummyMixin, AudioEventTest):
    pass


# TODO: this is really a mixer scaling test, has nothing to do with audio
class MixerTest(BaseTest):
    def test_set_volume(self):
        for value in range(0, 101):
            self.assertTrue(self.audio.set_volume(value).get())
            self.assertEqual(value, self.audio.get_volume().get())

    def test_set_volume_with_mixer_max_below_100(self):
        config = {
            'audio': {
                'mixer': 'fakemixer track_max_volume=40',
                'mixer_track': None,
                'mixer_volume': None,
                'output': 'fakesink',
                'visualizer': None,
            }
        }
        self.audio = self.audio_class.start(config=config).proxy()

        for value in range(0, 101):
            self.assertTrue(self.audio.set_volume(value).get())
            self.assertEqual(value, self.audio.get_volume().get())

    def test_set_volume_with_mixer_min_equal_max(self):
        config = {
            'audio': {
                'mixer': 'fakemixer track_max_volume=0',
                'mixer_track': None,
                'mixer_volume': None,
                'output': 'fakesink',
                'visualizer': None,
            }
        }
        self.audio = self.audio_class.start(config=config).proxy()
        self.assertEqual(0, self.audio.get_volume().get())


class AudioStateTest(unittest.TestCase):
    def setUp(self):
        self.audio = audio.Audio(config=None)

    def test_state_starts_as_stopped(self):
        self.assertEqual(audio.PlaybackState.STOPPED, self.audio.state)

    def test_state_does_not_change_when_in_gst_ready_state(self):
        self.audio._on_playbin_state_changed(
            gst.STATE_NULL, gst.STATE_READY, gst.STATE_VOID_PENDING)

        self.assertEqual(audio.PlaybackState.STOPPED, self.audio.state)

    def test_state_changes_from_stopped_to_playing_on_play(self):
        self.audio._on_playbin_state_changed(
            gst.STATE_NULL, gst.STATE_READY, gst.STATE_PLAYING)
        self.audio._on_playbin_state_changed(
            gst.STATE_READY, gst.STATE_PAUSED, gst.STATE_PLAYING)
        self.audio._on_playbin_state_changed(
            gst.STATE_PAUSED, gst.STATE_PLAYING, gst.STATE_VOID_PENDING)

        self.assertEqual(audio.PlaybackState.PLAYING, self.audio.state)

    def test_state_changes_from_playing_to_paused_on_pause(self):
        self.audio.state = audio.PlaybackState.PLAYING

        self.audio._on_playbin_state_changed(
            gst.STATE_PLAYING, gst.STATE_PAUSED, gst.STATE_VOID_PENDING)

        self.assertEqual(audio.PlaybackState.PAUSED, self.audio.state)

    def test_state_changes_from_playing_to_stopped_on_stop(self):
        self.audio.state = audio.PlaybackState.PLAYING

        self.audio._on_playbin_state_changed(
            gst.STATE_PLAYING, gst.STATE_PAUSED, gst.STATE_NULL)
        self.audio._on_playbin_state_changed(
            gst.STATE_PAUSED, gst.STATE_READY, gst.STATE_NULL)
        # We never get the following call, so the logic must work without it
        #self.audio._on_playbin_state_changed(
        #    gst.STATE_READY, gst.STATE_NULL, gst.STATE_VOID_PENDING)

        self.assertEqual(audio.PlaybackState.STOPPED, self.audio.state)
