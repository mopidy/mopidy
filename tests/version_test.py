from distutils.version import StrictVersion as SV
import platform

from mopidy import get_plain_version, get_platform, get_python

from tests import unittest


class VersionTest(unittest.TestCase):
    def test_current_version_is_parsable_as_a_strict_version_number(self):
        SV(get_plain_version())

    def test_versions_can_be_strictly_ordered(self):
        self.assert_(SV('0.1.0a0') < SV('0.1.0a1'))
        self.assert_(SV('0.1.0a1') < SV('0.1.0a2'))
        self.assert_(SV('0.1.0a2') < SV('0.1.0a3'))
        self.assert_(SV('0.1.0a3') < SV('0.1.0'))
        self.assert_(SV('0.1.0') < SV('0.2.0'))
        self.assert_(SV('0.1.0') < SV('1.0.0'))
        self.assert_(SV('0.2.0') < SV('0.3.0'))
        self.assert_(SV('0.3.0') < SV('0.3.1'))
        self.assert_(SV('0.3.1') < SV('0.4.0'))
        self.assert_(SV('0.4.0') < SV('0.4.1'))
        self.assert_(SV('0.4.1') < SV('0.5.0'))
        self.assert_(SV('0.5.0') < SV('0.6.0'))
        self.assert_(SV('0.6.0') < SV('0.6.1'))
        self.assert_(SV('0.6.1') < SV(get_plain_version()))
        self.assert_(SV(get_plain_version()) < SV('0.7.1'))

    def test_get_platform_contains_platform(self):
        self.assert_(platform.platform() in get_platform())

    def test_get_python_contains_python_implementation(self):
        self.assert_(platform.python_implementation() in get_python())

    def test_get_python_contains_python_version(self):
        self.assert_(platform.python_version() in get_python())
