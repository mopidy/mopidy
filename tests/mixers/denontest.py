import unittest
import os

from mopidy.mixers.denon import DenonMixer

class DenonMixerDeviceMock(object):
    def __init__(self):
        self._open = True
        self.ret_val = bytes('00')

    def write(self, x):
        pass
    def read(self, x):
        return self.ret_val
    def isOpen(self):
        return self._open
    def open(self):
        self._open = True

class DenonMixerTest(unittest.TestCase):
    def setUp(self):
        self.m = DenonMixer()
        self.m._device = DenonMixerDeviceMock()

    def test_volume_is_None_initially(self):
        self.assertEqual(self.m.volume, None)

    def test_volume_set_to_min(self):
        self.m.volume = 0
        self.assertEqual(self.m.volume, 0)

    def test_volume_set_to_max(self):
        self.m.volume = 100
        self.assertEqual(self.m.volume, 99)

    def test_volume_set_to_below_min_results_in_min(self):
        self.m.volume = -10
        self.assertEqual(self.m.volume, 0)

    def test_volume_set_to_above_max_results_in_max(self):
        self.m.volume = 110
        self.assertEqual(self.m.volume, 99)

    def test_reopen_device(self):
        self.m._device._open = False
        self.m.volume = 10
        self.assertTrue(self.m._device._open)
