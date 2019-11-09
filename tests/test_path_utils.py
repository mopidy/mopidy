import os
import unittest

from tests import path_utils


# TODO: kill this in favour of just os.path.getmtime + mocks
class MtimeTest(unittest.TestCase):
    def tearDown(self):  # noqa: N802
        path_utils.mtime.undo_fake()

    def test_mtime_of_current_dir(self):
        mtime_dir = int(os.stat(".").st_mtime)
        assert mtime_dir == path_utils.mtime(".")

    def test_fake_time_is_returned(self):
        path_utils.mtime.set_fake_time(123456)
        assert path_utils.mtime(".") == 123456
