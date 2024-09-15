import subprocess
import sys
import unittest
from pathlib import Path

import mopidy


class HelpTest(unittest.TestCase):
    def test_help_has_mopidy_options(self):
        mopidy_dir = Path(mopidy.__file__).parent
        process = subprocess.Popen(  # noqa: S603
            [sys.executable, "-m", "mopidy", "--help"],
            stdout=subprocess.PIPE,
            cwd=mopidy_dir.parent,
        )
        output = process.communicate()[0]
        assert b"--version" in output
        assert b"--help" in output
        assert b"--quiet" in output
        assert b"--verbose" in output
        assert b"--config" in output
        assert b"--option" in output
