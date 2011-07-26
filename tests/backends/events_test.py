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
            'track_playback_paused': threading.Event(),
            'track_playback_resumed': threading.Event(),
            'track_playback_started': threading.Event(),
            'track_playback_ended': threading.Event(),
        }
        self.backend = DummyBackend.start().proxy()
        self.listener = DummyBackendListener.start(self.events).proxy()

    def tearDown(self):
        ActorRegistry.stop_all()

    def test_pause_sends_track_playback_paused_event(self):
        self.backend.current_playlist.add([Track(uri='a')])
        self.backend.playback.play()
        self.backend.playback.pause()
        self.events['track_playback_paused'].wait(timeout=1)
        self.assertTrue(self.events['track_playback_paused'].is_set())

    def test_resume_sends_track_playback_resumed(self):
        self.backend.current_playlist.add([Track(uri='a')])
        self.backend.playback.play()
        self.backend.playback.pause()
        self.backend.playback.resume()
        self.events['track_playback_resumed'].wait(timeout=1)
        self.assertTrue(self.events['track_playback_resumed'].is_set())

    def test_play_sends_track_playback_started_event(self):
        self.backend.current_playlist.add([Track(uri='a')])
        self.backend.playback.play()
        self.events['track_playback_started'].wait(timeout=1)
        self.assertTrue(self.events['track_playback_started'].is_set())

    def test_stop_sends_track_playback_ended_event(self):
        self.backend.current_playlist.add([Track(uri='a')])
        self.backend.playback.play()
        self.backend.playback.stop()
        self.events['track_playback_ended'].wait(timeout=1)
        self.assertTrue(self.events['track_playback_ended'].is_set())


class DummyBackendListener(ThreadingActor, BackendListener):
    def __init__(self, events):
        self.events = events

    def track_playback_paused(self, track, time_position):
        self.events['track_playback_paused'].set()

    def track_playback_resumed(self, track, time_position):
        self.events['track_playback_resumed'].set()

    def track_playback_started(self, track):
        self.events['track_playback_started'].set()

    def track_playback_ended(self, track, time_position):
        self.events['track_playback_ended'].set()
