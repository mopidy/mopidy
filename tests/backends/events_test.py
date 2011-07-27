import mock
import unittest

from pykka.registry import ActorRegistry

from mopidy import listeners
from mopidy.backends.dummy import DummyBackend
from mopidy.models import Track

class BackendEventsTest(unittest.TestCase):
    def setUp(self):
        self.listener_send = mock.Mock()
        listeners.BackendListener.send = self.listener_send
        self.backend = DummyBackend.start().proxy()

    def tearDown(self):
        ActorRegistry.stop_all()

    def test_pause_sends_track_playback_paused_event(self):
        self.backend.current_playlist.add(Track(uri='a'))
        self.backend.playback.play().get()
        self.listener_send.reset_mock()
        self.backend.playback.pause().get()
        self.assertEqual(self.listener_send.call_args[0][0],
            'track_playback_paused')

    def test_resume_sends_track_playback_resumed(self):
        self.backend.current_playlist.add(Track(uri='a'))
        self.backend.playback.play()
        self.backend.playback.pause().get()
        self.listener_send.reset_mock()
        self.backend.playback.resume().get()
        self.assertEqual(self.listener_send.call_args[0][0],
            'track_playback_resumed')

    def test_play_sends_track_playback_started_event(self):
        self.backend.current_playlist.add(Track(uri='a'))
        self.listener_send.reset_mock()
        self.backend.playback.play().get()
        self.assertEqual(self.listener_send.call_args[0][0],
            'track_playback_started')

    def test_stop_sends_track_playback_ended_event(self):
        self.backend.current_playlist.add(Track(uri='a'))
        self.backend.playback.play().get()
        self.listener_send.reset_mock()
        self.backend.playback.stop().get()
        self.assertEqual(self.listener_send.call_args_list[0][0][0],
            'track_playback_ended')

    def test_seek_sends_seeked_event(self):
        self.backend.current_playlist.add(Track(uri='a', length=40000))
        self.backend.playback.play().get()
        self.listener_send.reset_mock()
        self.backend.playback.seek(1000).get()
        self.assertEqual(self.listener_send.call_args[0][0], 'seeked')
