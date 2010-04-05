import unittest

from mopidy.mixers.dummy import DummyMixer

class BaseMixerTest(unittest.TestCase):
    def setUp(self):
        self.m = DummyMixer()

    def test_volume_is_None_initially(self):
        self.assertEqual(self.m.volume, None)

    def test_volume_set_to_min(self):
        self.m.volume = 0
        self.assertEqual(self.m.volume, 0)

    def test_volume_set_to_max(self):
        self.m.volume = 100
        self.assertEqual(self.m.volume, 100)

    def test_volume_set_to_below_min_results_in_min(self):
        self.m.volume = -10
        self.assertEqual(self.m.volume, 0)

    def test_volume_set_to_above_max_results_in_max(self):
        self.m.volume = 110
        self.assertEqual(self.m.volume, 100)
