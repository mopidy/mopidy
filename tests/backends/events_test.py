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
            'started_playing': threading.Event(),
            'stopped_playing': threading.Event(),
        }
        self.backend = DummyBackend.start().proxy()
        self.listener = DummyBackendListener.start(self.events).proxy()

    def tearDown(self):
        ActorRegistry.stop_all()

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

    def started_playing(self, track):
        self.events['started_playing'].set()

    def stopped_playing(self, track, stop_position):
        self.events['stopped_playing'].set()
