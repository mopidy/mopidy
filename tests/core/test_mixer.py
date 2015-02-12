from __future__ import absolute_import, unicode_literals

import unittest

from mopidy import core


class CoreMixerTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.core = core.Core(mixer=None, backends=[])

    def test_volume(self):
        self.assertEqual(self.core.mixer.get_volume(), None)

        self.core.mixer.set_volume(30)

        self.assertEqual(self.core.mixer.get_volume(), 30)

        self.core.mixer.set_volume(70)

        self.assertEqual(self.core.mixer.get_volume(), 70)

    def test_mute(self):
        self.assertEqual(self.core.mixer.get_mute(), False)

        self.core.mixer.set_mute(True)

        self.assertEqual(self.core.mixer.get_mute(), True)
