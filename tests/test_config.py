import subprocess
import sys
import unittest
from pathlib import Path

import mopidy


class SubcommandConfigTest(unittest.TestCase):
    def test_mopidy_config_subcommand(self):
        mopidy_dir = Path(mopidy.__file__).parent
        process = subprocess.Popen(  # noqa: S603
            [sys.executable, "-m", "mopidy", "config"],
            stdout=subprocess.PIPE,
            cwd=mopidy_dir.parent,
        )
        output = process.communicate()[0]
        assert b"[core]" in output
        assert b"[logging]" in output
        assert b"[audio]" in output

    def test_mopidy_config_subcommand_bad_config(self):
        mopidy_dir = Path(mopidy.__file__).parent
        process = subprocess.Popen(  # noqa: S603
            [sys.executable, "-m", "mopidy", "-o core/cache_dir=$FOO", "config"],
            stdout=subprocess.PIPE,
            cwd=mopidy_dir.parent,
        )
        output = process.communicate()[0]
        assert b"[core]" in output
        assert b"[logging]" in output
        assert b"[audio]" in output
