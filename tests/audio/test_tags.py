import pytest

from mopidy._lib.gi import Gst
from mopidy.audio import tags
from mopidy.models import Track
from mopidy.types import DurationMs, Uri

DEPRECATION_MATCH = r"mopidy\.media\.Reader\.create\(\)"


def test_repr_tags_truncates_bytes_to_max_bytes():
    with pytest.deprecated_call(match=DEPRECATION_MATCH):
        result = tags.repr_tags({"image": [b"0123456789abcdef"]}, max_bytes=4)

    assert result == "{'image': [b'0123...']}"


def test_convert_taglist_converts_to_plain_types():
    taglist = Gst.TagList.new_empty()
    taglist.add_value(Gst.TagMergeMode.APPEND, Gst.TAG_TITLE, "a title")

    with pytest.deprecated_call(match=DEPRECATION_MATCH):
        result = tags.convert_taglist(taglist)

    assert result == {Gst.TAG_TITLE: ["a title"]}


def test_convert_tags_to_track_takes_a_length_and_a_last_modified():
    with pytest.deprecated_call(match=DEPRECATION_MATCH):
        track = tags.convert_tags_to_track(
            {Gst.TAG_TITLE: ["a title"]},
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
