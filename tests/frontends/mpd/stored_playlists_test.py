from __future__ import unicode_literals

import unittest

from mopidy.frontends.mpd.dispatcher import MpdContext, MpdDispatcher


class MpdContextTest(unittest.TestCase):
    def setUp(self):
        config = {
            'mpd': {
                'password': None,
            }
        }
        dispatcher = MpdDispatcher(config=config)
        self.context = dispatcher.context

    def test_create_unique_name_replaces_newlines_with_space(self):
        result = self.context.create_unique_name("playlist name\n")
        self.assertEqual("playlist name ", result)

    def test_create_unique_name_replaces_carriage_returns_with_space(self):
        result = self.context.create_unique_name("playlist name\r")
        self.assertEqual("playlist name ", result)

    def test_create_unique_name_replaces_forward_slashes_with_space(self):
        result = self.context.create_unique_name("playlist name/")
        self.assertEqual("playlist name ", result)
