from __future__ import absolute_import, unicode_literals

import unittest

import mock

from mopidy import core, mixer


class CoreMixerTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.mixer = mock.Mock(spec=mixer.Mixer)
        self.core = core.Core(mixer=self.mixer, backends=[])

    def test_get_volume(self):
        self.mixer.get_volume.return_value.get.return_value = 30

        self.assertEqual(self.core.mixer.get_volume(), 30)
        self.mixer.get_volume.assert_called_once_with()

    def test_set_volume(self):
        self.core.mixer.set_volume(30)

        self.mixer.set_volume.assert_called_once_with(30)

    def test_get_mute(self):
        self.mixer.get_mute.return_value.get.return_value = True

        self.assertEqual(self.core.mixer.get_mute(), True)
        self.mixer.get_mute.assert_called_once_with()

    def test_set_mute(self):
        self.core.mixer.set_mute(True)

        self.mixer.set_mute.assert_called_once_with(True)
