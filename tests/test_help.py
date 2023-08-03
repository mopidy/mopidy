import os
import subprocess
import sys
import unittest
from pathlib import Path

import mopidy


class HelpTest(unittest.TestCase):
    def test_help_has_mopidy_options(self):
        mopidy_dir = Path(mopidy.__file__).parent
        args = [sys.executable, mopidy_dir, "--help"]
        process = subprocess.Popen(
            args,
            env={
                "PYTHONPATH": ":".join(
                    [
                        str(mopidy_dir.parent),
                        os.environ.get("PYTHONPATH", ""),
                    ]
                )
            },
            stdout=subprocess.PIPE,
        )
        output = process.communicate()[0]
        assert b"--version" in output
        assert b"--help" in output
        assert b"--quiet" in output
        assert b"--verbose" in output
        assert b"--config" in output
        assert b"--option" in output
