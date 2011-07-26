import unittest

from mopidy.listeners import BackendListener
from mopidy.models import Track

class BackendListenerTest(unittest.TestCase):
    def setUp(self):
        self.listener = BackendListener()

    def test_listener_has_default_impl_for_the_track_playback_paused_event(self):
        self.listener.track_playback_paused(Track(), 0)

    def test_listener_has_default_impl_for_the_track_playback_resumed_event(self):
        self.listener.track_playback_resumed(Track(), 0)

    def test_listener_has_default_impl_for_the_track_playback_started(self):
        self.listener.track_playback_started(Track())

    def test_listener_has_default_impl_for_the_track_playback_ended(self):
        self.listener.track_playback_ended(Track(), 0)
