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
        self.assertIn('--version', output)
        self.assertIn('--help', output)
        self.assertIn('--help-gst', output)
        self.assertIn('--interactive', output)
        self.assertIn('--quiet', output)
        self.assertIn('--verbose', output)
        self.assertIn('--save-debug-log', output)
        self.assertIn('--list-settings', output)

    def test_help_gst_has_gstreamer_options(self):
        mopidy_dir = os.path.dirname(mopidy.__file__)
        args = [sys.executable, mopidy_dir, '--help-gst']
        process = subprocess.Popen(args, stdout=subprocess.PIPE)
        output = process.communicate()[0]
        self.assertIn('--gst-version', output)
