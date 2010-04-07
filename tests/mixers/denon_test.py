import unittest

from mopidy.mixers.denon import DenonMixer

class DenonMixerDeviceMock(object):
    def __init__(self):
        self._open = True
        self.ret_val = bytes('MV00\r')

    def write(self, x):
        if x[2] != '?':
            self.ret_val = bytes(x)

    def read(self, x):
        return self.ret_val

    def readline(self):
        return self.ret_val

    def isOpen(self):
        return self._open

    def open(self):
        self._open = True

class DenonMixerTest(unittest.TestCase):
    def setUp(self):
        self.device = DenonMixerDeviceMock()
        self.mixer = DenonMixer(device=self.device)

    def test_volume_set_to_min(self):
        self.mixer.volume = 0
        self.assertEqual(self.mixer.volume, 0)

    def test_volume_set_to_max(self):
        self.mixer.volume = 100
        self.assertEqual(self.mixer.volume, 99)

    def test_volume_set_to_below_min_results_in_min(self):
        self.mixer.volume = -10
        self.assertEqual(self.mixer.volume, 0)

    def test_volume_set_to_above_max_results_in_max(self):
        self.mixer.volume = 110
        self.assertEqual(self.mixer.volume, 99)

    def test_reopen_device(self):
        self.device._open = False
        self.mixer.volume = 10
        self.assertTrue(self.device.isOpen())
