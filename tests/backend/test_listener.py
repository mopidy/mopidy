from __future__ import unicode_literals

import mock
import unittest

from mopidy import backend


class BackendListenerTest(unittest.TestCase):
    def setUp(self):
        self.listener = backend.BackendListener()

    def test_on_event_forwards_to_specific_handler(self):
        self.listener.playlists_loaded = mock.Mock()

        self.listener.on_event('playlists_loaded')

        self.listener.playlists_loaded.assert_called_with()

    def test_listener_has_default_impl_for_playlists_loaded(self):
        self.listener.playlists_loaded()
