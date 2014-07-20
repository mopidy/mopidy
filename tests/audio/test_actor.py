from __future__ import unicode_literals

import unittest

import gobject
gobject.threads_init()

import pygst
pygst.require('0.10')
import gst  # noqa

import mock

import pykka

from mopidy import audio
from mopidy.utils.path import path_to_uri

from tests import path_to_data_dir


class AudioTest(unittest.TestCase):
    def setUp(self):
        config = {
            'audio': {
                'mixer': 'foomixer',
                'mixer_volume': None,
                'output': 'fakesink',
                'visualizer': None,
            },
            'proxy': {
                'hostname': '',
            },
        }
        self.song_uri = path_to_uri(path_to_data_dir('song1.wav'))
        self.audio = audio.Audio.start(config=config, mixer=None).proxy()

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def prepare_uri(self, uri):
        self.audio.prepare_change()
        self.audio.set_uri(uri)

    def test_start_playback_existing_file(self):
        self.prepare_uri(self.song_uri)
        self.assertTrue(self.audio.start_playback().get())

    def test_start_playback_non_existing_file(self):
        self.prepare_uri(self.song_uri + 'bogus')
        self.assertFalse(self.audio.start_playback().get())

    def test_pause_playback_while_playing(self):
        self.prepare_uri(self.song_uri)
        self.audio.start_playback()
        self.assertTrue(self.audio.pause_playback().get())

    def test_stop_playback_while_playing(self):
        self.prepare_uri(self.song_uri)
        self.audio.start_playback()
        self.assertTrue(self.audio.stop_playback().get())

    @unittest.SkipTest
    def test_deliver_data(self):
        pass  # TODO

    @unittest.SkipTest
    def test_end_of_data_stream(self):
        pass  # TODO

    def test_set_volume(self):
        for value in range(0, 101):
            self.assertTrue(self.audio.set_volume(value).get())
            self.assertEqual(value, self.audio.get_volume().get())

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
    def setUp(self):
        self.audio = audio.Audio(config=None, mixer=None)

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
        # self.audio._on_playbin_state_changed(
        #     gst.STATE_READY, gst.STATE_NULL, gst.STATE_VOID_PENDING)

        self.assertEqual(audio.PlaybackState.STOPPED, self.audio.state)


class AudioBufferingTest(unittest.TestCase):
    def setUp(self):
        self.audio = audio.Audio(config=None, mixer=None)
        self.audio._playbin = mock.Mock(spec=['set_state'])

    def test_pause_when_buffer_empty(self):
        playbin = self.audio._playbin
        self.audio.start_playback()
        playbin.set_state.assert_called_with(gst.STATE_PLAYING)
        playbin.set_state.reset_mock()

        self.audio._on_buffering(0)
        playbin.set_state.assert_called_with(gst.STATE_PAUSED)
        self.assertTrue(self.audio._buffering)

    def test_stay_paused_when_buffering_finished(self):
        playbin = self.audio._playbin
        self.audio.pause_playback()
        playbin.set_state.assert_called_with(gst.STATE_PAUSED)
        playbin.set_state.reset_mock()

        self.audio._on_buffering(100)
        self.assertEqual(playbin.set_state.call_count, 0)
        self.assertFalse(self.audio._buffering)

    def test_change_to_paused_while_buffering(self):
        playbin = self.audio._playbin
        self.audio.start_playback()
        playbin.set_state.assert_called_with(gst.STATE_PLAYING)
        playbin.set_state.reset_mock()

        self.audio._on_buffering(0)
        playbin.set_state.assert_called_with(gst.STATE_PAUSED)
        self.audio.pause_playback()
        playbin.set_state.reset_mock()

        self.audio._on_buffering(100)
        self.assertEqual(playbin.set_state.call_count, 0)
        self.assertFalse(self.audio._buffering)

    def test_change_to_stopped_while_buffering(self):
        playbin = self.audio._playbin
        self.audio.start_playback()
        playbin.set_state.assert_called_with(gst.STATE_PLAYING)
        playbin.set_state.reset_mock()

        self.audio._on_buffering(0)
        playbin.set_state.assert_called_with(gst.STATE_PAUSED)
        playbin.set_state.reset_mock()

        self.audio.stop_playback()
        playbin.set_state.assert_called_with(gst.STATE_NULL)
        self.assertFalse(self.audio._buffering)
