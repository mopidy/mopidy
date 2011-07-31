import mock

from pykka.registry import ActorRegistry

from mopidy.backends.dummy import DummyBackend
from mopidy.listeners import BackendListener
from mopidy.models import Track

from tests import unittest


@mock.patch.object(BackendListener, 'send')
class BackendEventsTest(unittest.TestCase):
    def setUp(self):
        self.backend = DummyBackend.start().proxy()

    def tearDown(self):
        ActorRegistry.stop_all()

    def test_pause_sends_track_playback_paused_event(self, send):
        self.backend.current_playlist.add(Track(uri='a'))
        self.backend.playback.play().get()
        send.reset_mock()
        self.backend.playback.pause().get()
        self.assertEqual(send.call_args[0][0], 'track_playback_paused')

    def test_resume_sends_track_playback_resumed(self, send):
        self.backend.current_playlist.add(Track(uri='a'))
        self.backend.playback.play()
        self.backend.playback.pause().get()
        send.reset_mock()
        self.backend.playback.resume().get()
        self.assertEqual(send.call_args[0][0], 'track_playback_resumed')

    def test_play_sends_track_playback_started_event(self, send):
        self.backend.current_playlist.add(Track(uri='a'))
        send.reset_mock()
        self.backend.playback.play().get()
        self.assertEqual(send.call_args[0][0], 'track_playback_started')

    def test_stop_sends_track_playback_ended_event(self, send):
        self.backend.current_playlist.add(Track(uri='a'))
        self.backend.playback.play().get()
        send.reset_mock()
        self.backend.playback.stop().get()
        self.assertEqual(send.call_args_list[0][0][0], 'track_playback_ended')

    def test_seek_sends_seeked_event(self, send):
        self.backend.current_playlist.add(Track(uri='a', length=40000))
        self.backend.playback.play().get()
        send.reset_mock()
        self.backend.playback.seek(1000).get()
        self.assertEqual(send.call_args[0][0], 'seeked')
