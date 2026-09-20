"""The public tag helpers. The code is covered by
tests/audio/_gst/test_tags.py.
"""

from mopidy.audio import tags
from mopidy.models import Track
from mopidy.types import DurationMs, Uri


def test_repr_tags_truncates_bytes_to_max_bytes():
    assert tags.repr_tags({"image": [b"0123456789abcdef"]}, max_bytes=4) == (
        "{'image': [b'0123...']}"
    )


def test_convert_tags_to_track_takes_a_length_and_a_last_modified():
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
