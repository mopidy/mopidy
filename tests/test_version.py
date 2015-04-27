from __future__ import absolute_import, unicode_literals

import unittest
from distutils.version import StrictVersion

from mopidy import __version__


class VersionTest(unittest.TestCase):

    def assertVersionLess(self, first, second):  # noqa: N802
        self.assertLess(StrictVersion(first), StrictVersion(second))

    def test_current_version_is_parsable_as_a_strict_version_number(self):
        StrictVersion(__version__)

    def test_versions_can_be_strictly_ordered(self):
        self.assertVersionLess('0.1.0a0', '0.1.0a1')
        self.assertVersionLess('0.1.0a1', '0.1.0a2')
        self.assertVersionLess('0.1.0a2', '0.1.0a3')
        self.assertVersionLess('0.1.0a3', '0.1.0')
        self.assertVersionLess('0.1.0', '0.2.0')
        self.assertVersionLess('0.1.0', '1.0.0')
        self.assertVersionLess('0.2.0', '0.3.0')
        self.assertVersionLess('0.3.0', '0.3.1')
        self.assertVersionLess('0.3.1', '0.4.0')
        self.assertVersionLess('0.4.0', '0.4.1')
        self.assertVersionLess('0.4.1', '0.5.0')
        self.assertVersionLess('0.5.0', '0.6.0')
        self.assertVersionLess('0.6.0', '0.6.1')
        self.assertVersionLess('0.6.1', '0.7.0')
        self.assertVersionLess('0.7.0', '0.7.1')
        self.assertVersionLess('0.7.1', '0.7.2')
        self.assertVersionLess('0.7.2', '0.7.3')
        self.assertVersionLess('0.7.3', '0.8.0')
        self.assertVersionLess('0.8.0', '0.8.1')
        self.assertVersionLess('0.8.1', '0.9.0')
        self.assertVersionLess('0.9.0', '0.10.0')
        self.assertVersionLess('0.10.0', '0.11.0')
        self.assertVersionLess('0.11.0', '0.11.1')
        self.assertVersionLess('0.11.1', '0.12.0')
        self.assertVersionLess('0.12.0', '0.13.0')
        self.assertVersionLess('0.13.0', '0.14.0')
        self.assertVersionLess('0.14.0', '0.14.1')
        self.assertVersionLess('0.14.1', '0.14.2')
        self.assertVersionLess('0.14.2', '0.15.0')
        self.assertVersionLess('0.15.0', '0.16.0')
        self.assertVersionLess('0.16.0', '0.17.0')
        self.assertVersionLess('0.17.0', '0.18.0')
        self.assertVersionLess('0.18.0', '0.18.1')
        self.assertVersionLess('0.18.1', '0.18.2')
        self.assertVersionLess('0.18.2', '0.18.3')
        self.assertVersionLess('0.18.3', '0.19.0')
        self.assertVersionLess('0.19.0', '0.19.1')
        self.assertVersionLess('0.19.1', '0.19.2')
        self.assertVersionLess('0.19.2', '0.19.3')
        self.assertVersionLess('0.19.3', '0.19.4')
        self.assertVersionLess('0.19.4', '0.19.5')
        self.assertVersionLess('0.19.5', '1.0.0')
        self.assertVersionLess('1.0.0', '1.0.1')
        self.assertVersionLess('1.0.1', '1.0.2')
        self.assertVersionLess('1.0.2', __version__)
        self.assertVersionLess(__version__, '1.0.4')
