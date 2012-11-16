from __future__ import unicode_literals

from mopidy.backends.listener import BackendListener

from tests import unittest


class CoreListenerTest(unittest.TestCase):
    def setUp(self):
        self.listener = BackendListener()

    def test_listener_has_default_impl_for_playlists_loaded(self):
        self.listener.playlists_loaded()
