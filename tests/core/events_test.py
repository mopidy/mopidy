from __future__ import unicode_literals

import mock
import pykka

from mopidy import audio, core
from mopidy.backends import dummy
from mopidy.models import Track

from tests import unittest


@mock.patch.object(core.CoreListener, 'send')
class BackendEventsTest(unittest.TestCase):
    def setUp(self):
        self.audio = mock.Mock(spec=audio.Audio)
        self.backend = dummy.DummyBackend.start(audio=audio).proxy()
        self.core = core.Core.start(backends=[self.backend]).proxy()

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_pause_sends_track_playback_paused_event(self, send):
        self.core.tracklist.add(Track(uri='dummy:a'))
        self.core.playback.play().get()
        send.reset_mock()
        self.core.playback.pause().get()
        self.assertEqual(send.call_args[0][0], 'track_playback_paused')

    def test_resume_sends_track_playback_resumed(self, send):
        self.core.tracklist.add(Track(uri='dummy:a'))
        self.core.playback.play()
        self.core.playback.pause().get()
        send.reset_mock()
        self.core.playback.resume().get()
        self.assertEqual(send.call_args[0][0], 'track_playback_resumed')

    def test_play_sends_track_playback_started_event(self, send):
        self.core.tracklist.add(Track(uri='dummy:a'))
        send.reset_mock()
        self.core.playback.play().get()
        self.assertEqual(send.call_args[0][0], 'track_playback_started')

    def test_stop_sends_track_playback_ended_event(self, send):
        self.core.tracklist.add(Track(uri='dummy:a'))
        self.core.playback.play().get()
        send.reset_mock()
        self.core.playback.stop().get()
        self.assertEqual(send.call_args_list[0][0][0], 'track_playback_ended')

    def test_seek_sends_seeked_event(self, send):
        self.core.tracklist.add(Track(uri='dummy:a', length=40000))
        self.core.playback.play().get()
        send.reset_mock()
        self.core.playback.seek(1000).get()
        self.assertEqual(send.call_args[0][0], 'seeked')

    def test_tracklist_add_sends_tracklist_changed_event(self, send):
        send.reset_mock()
        self.core.tracklist.add(Track(uri='dummy:a')).get()
        self.assertEqual(send.call_args[0][0], 'tracklist_changed')

    def test_tracklist_append_sends_tracklist_changed_event(self, send):
        send.reset_mock()
        self.core.tracklist.append([Track(uri='dummy:a')]).get()
        self.assertEqual(send.call_args[0][0], 'tracklist_changed')

    def test_tracklist_clear_sends_tracklist_changed_event(self, send):
        self.core.tracklist.append([Track(uri='dummy:a')]).get()
        send.reset_mock()
        self.core.tracklist.clear().get()
        self.assertEqual(send.call_args[0][0], 'tracklist_changed')

    def test_tracklist_move_sends_tracklist_changed_event(self, send):
        self.core.tracklist.append(
            [Track(uri='dummy:a'), Track(uri='dummy:b')]).get()
        send.reset_mock()
        self.core.tracklist.move(0, 1, 1).get()
        self.assertEqual(send.call_args[0][0], 'tracklist_changed')

    def test_tracklist_remove_sends_tracklist_changed_event(self, send):
        self.core.tracklist.append([Track(uri='dummy:a')]).get()
        send.reset_mock()
        self.core.tracklist.remove(uri='dummy:a').get()
        self.assertEqual(send.call_args[0][0], 'tracklist_changed')

    def test_tracklist_shuffle_sends_tracklist_changed_event(self, send):
        self.core.tracklist.append(
            [Track(uri='dummy:a'), Track(uri='dummy:b')]).get()
        send.reset_mock()
        self.core.tracklist.shuffle().get()
        self.assertEqual(send.call_args[0][0], 'tracklist_changed')
