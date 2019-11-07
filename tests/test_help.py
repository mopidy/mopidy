from __future__ import absolute_import, unicode_literals

import os
import subprocess
import sys
import unittest

import mopidy


class HelpTest(unittest.TestCase):
    def test_help_has_mopidy_options(self):
        mopidy_dir = os.path.dirname(mopidy.__file__)
        args = [sys.executable, mopidy_dir, "--help"]
        process = subprocess.Popen(
            args,
            env={
                "PYTHONPATH": ":".join(
                    [
                        os.path.join(mopidy_dir, ".."),
                        os.environ.get("PYTHONPATH", ""),
                    ]
                )
            },
            stdout=subprocess.PIPE,
        )
        output = process.communicate()[0]
        self.assertIn(b"--version", output)
        self.assertIn(b"--help", output)
        self.assertIn(b"--quiet", output)
        self.assertIn(b"--verbose", output)
        self.assertIn(b"--config", output)
        self.assertIn(b"--option", output)
