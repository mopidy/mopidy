import unittest

from mopidy.listeners import BackendListener
from mopidy.models import Track

class BackendListenerTest(unittest.TestCase):
    def setUp(self):
        self.listener = BackendListener()

    def test_listener_has_default_impl_for_the_paused_playing_event(self):
        self.listener.paused_playing(Track(), 0)

    def test_listener_has_default_impl_for_the_resumed_playing_event(self):
        self.listener.resumed_playing(Track(), 0)

    def test_listener_has_default_impl_for_the_started_playing_event(self):
        self.listener.started_playing(Track())

    def test_listener_has_default_impl_for_the_stopped_playing_event(self):
        self.listener.stopped_playing(Track(), 0)
