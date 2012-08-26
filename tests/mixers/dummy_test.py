from mopidy.mixers.dummy import DummyMixer

from tests import unittest
from tests.mixers.base_test import BaseMixerTest


class DummyMixerTest(BaseMixerTest, unittest.TestCase):
    mixer_class = DummyMixer

    def test_set_volume_is_capped(self):
        self.mixer.amplification_factor = 0.5
        self.mixer.volume = 100
        self.assertEquals(self.mixer._volume, 50)

    def test_get_volume_does_not_show_that_the_volume_is_capped(self):
        self.mixer.amplification_factor = 0.5
        self.mixer._volume = 50
        self.assertEquals(self.mixer.volume, 100)

    def test_get_volume_get_the_same_number_as_was_set(self):
        self.mixer.amplification_factor = 0.5
        self.mixer.volume = 13
        self.assertEquals(self.mixer.volume, 13)
