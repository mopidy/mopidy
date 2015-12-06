from __future__ import absolute_import, unicode_literals

import unittest
from distutils.version import StrictVersion

from mopidy import __version__


class VersionTest(unittest.TestCase):

    def test_current_version_is_parsable_as_a_strict_version_number(self):
        StrictVersion(__version__)
