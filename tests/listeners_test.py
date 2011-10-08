from mopidy.listeners import BackendListener
from mopidy.models import Track

from tests import unittest


class BackendListenerTest(unittest.TestCase):
    def setUp(self):
        self.listener = BackendListener()

    def test_listener_has_default_impl_for_track_playback_paused(self):
        self.listener.track_playback_paused(Track(), 0)

    def test_listener_has_default_impl_for_track_playback_resumed(self):
        self.listener.track_playback_resumed(Track(), 0)

    def test_listener_has_default_impl_for_track_playback_started(self):
        self.listener.track_playback_started(Track())

    def test_listener_has_default_impl_for_track_playback_ended(self):
        self.listener.track_playback_ended(Track(), 0)

    def test_listener_has_default_impl_for_playback_state_changed(self):
        self.listener.playback_state_changed()

    def test_listener_has_default_impl_for_playlist_changed(self):
        self.listener.playlist_changed()

    def test_listener_has_default_impl_for_options_changed(self):
        self.listener.options_changed()

    def test_listener_has_default_impl_for_volume_changed(self):
        self.listener.volume_changed()

    def test_listener_has_default_impl_for_seeked(self):
        self.listener.seeked()
