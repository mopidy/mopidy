import threading
import unittest

from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry

from mopidy.backends.dummy import DummyBackend
from mopidy.listeners import BackendListener
from mopidy.models import Track

class BackendEventsTest(unittest.TestCase):
    def setUp(self):
        self.events = {
            'paused_playing': threading.Event(),
            'resumed_playing': threading.Event(),
            'started_playing': threading.Event(),
            'stopped_playing': threading.Event(),
        }
        self.backend = DummyBackend.start().proxy()
        self.listener = DummyBackendListener.start(self.events).proxy()

    def tearDown(self):
        ActorRegistry.stop_all()

    def test_pause_sends_paused_playing_event(self):
        self.backend.current_playlist.add([Track(uri='a')])
        self.backend.playback.play()
        self.backend.playback.pause()
        self.events['paused_playing'].wait(timeout=1)
        self.assertTrue(self.events['paused_playing'].is_set())

    def test_resume_sends_resumed_playing_event(self):
        self.backend.current_playlist.add([Track(uri='a')])
        self.backend.playback.play()
        self.backend.playback.pause()
        self.backend.playback.resume()
        self.events['resumed_playing'].wait(timeout=1)
        self.assertTrue(self.events['resumed_playing'].is_set())

    def test_play_sends_started_playing_event(self):
        self.backend.current_playlist.add([Track(uri='a')])
        self.backend.playback.play()
        self.events['started_playing'].wait(timeout=1)
        self.assertTrue(self.events['started_playing'].is_set())

    def test_stop_sends_stopped_playing_event(self):
        self.backend.current_playlist.add([Track(uri='a')])
        self.backend.playback.play()
        self.backend.playback.stop()
        self.events['stopped_playing'].wait(timeout=1)
        self.assertTrue(self.events['stopped_playing'].is_set())


class DummyBackendListener(ThreadingActor, BackendListener):
    def __init__(self, events):
        self.events = events

    def paused_playing(self, track, time_position):
        self.events['paused_playing'].set()

    def resumed_playing(self, track, time_position):
        self.events['resumed_playing'].set()

    def started_playing(self, track):
        self.events['started_playing'].set()

    def stopped_playing(self, track, time_position):
        self.events['stopped_playing'].set()
