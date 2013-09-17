from __future__ import unicode_literals

import os
import subprocess
import sys
import unittest

import mopidy


class HelpTest(unittest.TestCase):
    def test_help_has_mopidy_options(self):
        mopidy_dir = os.path.dirname(mopidy.__file__)
        args = [sys.executable, mopidy_dir, '--help']
        process = subprocess.Popen(
            args,
            env={'PYTHONPATH': os.path.join(mopidy_dir, '..')},
            stdout=subprocess.PIPE)
        output = process.communicate()[0]
        self.assertIn('--version', output)
        self.assertIn('--help', output)
        self.assertIn('--quiet', output)
        self.assertIn('--verbose', output)
        self.assertIn('--save-debug-log', output)
        self.assertIn('--show-config', output)
        self.assertIn('--config', output)
        self.assertIn('--option', output)
