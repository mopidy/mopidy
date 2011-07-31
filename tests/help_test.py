import os
import subprocess
import sys

import mopidy

from tests import unittest


class HelpTest(unittest.TestCase):
    def test_help_has_mopidy_options(self):
        mopidy_dir = os.path.dirname(mopidy.__file__)
        args = [sys.executable, mopidy_dir, '--help']
        process = subprocess.Popen(args, stdout=subprocess.PIPE)
        output = process.communicate()[0]
        self.assert_('--version' in output)
        self.assert_('--help' in output)
        self.assert_('--help-gst' in output)
        self.assert_('--interactive' in output)
        self.assert_('--quiet' in output)
        self.assert_('--verbose' in output)
        self.assert_('--save-debug-log' in output)
        self.assert_('--list-settings' in output)

    def test_help_gst_has_gstreamer_options(self):
        mopidy_dir = os.path.dirname(mopidy.__file__)
        args = [sys.executable, mopidy_dir, '--help-gst']
        process = subprocess.Popen(args, stdout=subprocess.PIPE)
        output = process.communicate()[0]
        self.assert_('--gst-version' in output)
