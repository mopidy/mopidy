from mopidy.mixers.denon import DenonMixer
from tests.mixers.base_test import BaseMixerTest

from tests import unittest


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


class DenonMixerTest(BaseMixerTest, unittest.TestCase):
    ACTUAL_MAX = 99
    INITIAL = 1

    mixer_class = DenonMixer

    def setUp(self):
        self.device = DenonMixerDeviceMock()
        self.mixer = DenonMixer(device=self.device)

    def test_reopen_device(self):
        self.device._open = False
        self.mixer.volume = 10
        self.assertTrue(self.device.isOpen())
