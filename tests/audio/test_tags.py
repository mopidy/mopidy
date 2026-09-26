"""The deprecated tag helpers still work and still forward every argument.
The code is covered by tests/audio/_gst/test_tags.py.
"""

import pytest

from mopidy._lib.gi import Gst
from mopidy.audio import tags
from mopidy.models import Track
from mopidy.types import DurationMs, Uri


def test_repr_tags_truncates_bytes_to_max_bytes():
    with pytest.deprecated_call():
        result = tags.repr_tags({"image": [b"0123456789abcdef"]}, max_bytes=4)

    assert result == "{'image': [b'0123...']}"


def test_convert_taglist_converts_to_plain_types():
    taglist = Gst.TagList.new_empty()
    taglist.add_value(Gst.TagMergeMode.APPEND, "title", "a title")

    with pytest.deprecated_call():
        result = tags.convert_taglist(taglist)

    assert result == {"title": ["a title"]}


def test_convert_tags_to_track_takes_a_length_and_a_last_modified():
    with pytest.deprecated_call():
        track = tags.convert_tags_to_track(
            {"title": ["a title"]},
            uri=Uri("dummy:uri"),
            length=DurationMs(4704),
            last_modified=1234,
        )

    assert track == Track(
        uri=Uri("dummy:uri"),
        name="a title",
        length=DurationMs(4704),
        last_modified=1234,
    )
