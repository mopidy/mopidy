from __future__ import absolute_import, unicode_literals

import pytest

from mopidy.audio import utils
from mopidy.internal.gi import Gst


class TestCreateBuffer(object):

    def test_creates_buffer(self):
        buf = utils.create_buffer(b'123', timestamp=0, duration=1000000)

        assert isinstance(buf, Gst.Buffer)
        assert buf.pts == 0
        assert buf.duration == 1000000
        assert buf.get_size() == len(b'123')

    def test_fails_if_data_has_zero_length(self):
        with pytest.raises(ValueError) as excinfo:
            utils.create_buffer(b'', timestamp=0, duration=1000000)

        assert 'Cannot create buffer without data' in str(excinfo.value)
