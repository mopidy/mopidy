from __future__ import unicode_literals

from distutils.version import StrictVersion as SV
import unittest

from mopidy import __version__


class VersionTest(unittest.TestCase):
    def test_current_version_is_parsable_as_a_strict_version_number(self):
        SV(__version__)

    def test_versions_can_be_strictly_ordered(self):
        self.assertLess(SV('0.1.0a0'), SV('0.1.0a1'))
        self.assertLess(SV('0.1.0a1'), SV('0.1.0a2'))
        self.assertLess(SV('0.1.0a2'), SV('0.1.0a3'))
        self.assertLess(SV('0.1.0a3'), SV('0.1.0'))
        self.assertLess(SV('0.1.0'), SV('0.2.0'))
        self.assertLess(SV('0.1.0'), SV('1.0.0'))
        self.assertLess(SV('0.2.0'), SV('0.3.0'))
        self.assertLess(SV('0.3.0'), SV('0.3.1'))
        self.assertLess(SV('0.3.1'), SV('0.4.0'))
        self.assertLess(SV('0.4.0'), SV('0.4.1'))
        self.assertLess(SV('0.4.1'), SV('0.5.0'))
        self.assertLess(SV('0.5.0'), SV('0.6.0'))
        self.assertLess(SV('0.6.0'), SV('0.6.1'))
        self.assertLess(SV('0.6.1'), SV('0.7.0'))
        self.assertLess(SV('0.7.0'), SV('0.7.1'))
        self.assertLess(SV('0.7.1'), SV('0.7.2'))
        self.assertLess(SV('0.7.2'), SV('0.7.3'))
        self.assertLess(SV('0.7.3'), SV('0.8.0'))
        self.assertLess(SV('0.8.0'), SV('0.8.1'))
        self.assertLess(SV('0.8.1'), SV('0.9.0'))
        self.assertLess(SV('0.9.0'), SV('0.10.0'))
        self.assertLess(SV('0.10.0'), SV('0.11.0'))
        self.assertLess(SV('0.11.0'), SV('0.11.1'))
        self.assertLess(SV('0.11.1'), SV('0.12.0'))
        self.assertLess(SV('0.12.0'), SV('0.13.0'))
        self.assertLess(SV('0.13.0'), SV('0.14.0'))
        self.assertLess(SV('0.14.0'), SV('0.14.1'))
        self.assertLess(SV('0.14.1'), SV('0.14.2'))
        self.assertLess(SV('0.14.2'), SV('0.15.0'))
        self.assertLess(SV('0.15.0'), SV('0.16.0'))
        self.assertLess(SV('0.16.0'), SV(__version__))
        self.assertLess(SV(__version__), SV('0.17.1'))
