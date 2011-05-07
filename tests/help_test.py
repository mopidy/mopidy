import os
import subprocess
import sys
import unittest

import mopidy

class HelpTest(unittest.TestCase):
    def test_help_has_mopidy_options(self):
        mopidy_dir = os.path.dirname(mopidy.__file__)
        args = [sys.executable, mopidy_dir, '--help']
        process = subprocess.Popen(args, stdout=subprocess.PIPE)
        output = process.communicate()[0]
        self.assert_('--version' in output)
        self.assert_('--help' in output)
        self.assert_('--quiet' in output)
        self.assert_('--verbose' in output)
        self.assert_('--save-debug-log' in output)
        self.assert_('--list-settings' in output)
