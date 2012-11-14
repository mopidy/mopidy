from __future__ import unicode_literals

from mopidy import audio

from tests import unittest


class AudioListenerTest(unittest.TestCase):
    def setUp(self):
        self.listener = audio.AudioListener()

    def test_listener_has_default_impl_for_reached_end_of_stream(self):
        self.listener.reached_end_of_stream()

    def test_listener_has_default_impl_for_state_changed(self):
        self.listener.state_changed(None, None)
