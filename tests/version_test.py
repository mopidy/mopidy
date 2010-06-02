from distutils.version import StrictVersion as SV
import unittest

from mopidy import get_version

class VersionTest(unittest.TestCase):
    def test_current_version_is_parsable_as_a_strict_version_number(self):
        SV(get_version())

    def test_versions_can_be_strictly_ordered(self):
        self.assert_(SV('0.1.0a0') < SV('0.1.0a1'))
        self.assert_(SV('0.1.0a2') < SV(get_version()))
        self.assert_(SV(get_version()) < SV('0.1.0a4'))
        self.assert_(SV('0.1.0a0') < SV('0.1.0'))
        self.assert_(SV('0.1.0') < SV('0.1.1'))
        self.assert_(SV('0.1.1') < SV('0.2.0'))
        self.assert_(SV('0.2.0') < SV('1.0.0'))
