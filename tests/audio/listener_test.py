from __future__ import unicode_literals

import mock
import unittest

from mopidy import audio


class AudioListenerTest(unittest.TestCase):
    def setUp(self):
        self.listener = audio.AudioListener()

    def test_on_event_forwards_to_specific_handler(self):
        self.listener.state_changed = mock.Mock()

        self.listener.on_event(
            'state_changed', old_state='stopped', new_state='playing')

        self.listener.state_changed.assert_called_with(
            old_state='stopped', new_state='playing')

    def test_listener_has_default_impl_for_reached_end_of_stream(self):
        self.listener.reached_end_of_stream()

    def test_listener_has_default_impl_for_state_changed(self):
        self.listener.state_changed(None, None)
