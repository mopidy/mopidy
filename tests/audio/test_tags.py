from mopidy._lib import gst
from mopidy.audio import tags
from mopidy.media._gst import tags as media_tags


def test_repr_tags_is_available():
    assert tags.repr_tags is gst.repr_tags


def test_convert_taglist_is_available():
    assert tags.convert_taglist is gst.convert_taglist


def test_convert_tags_to_track_is_available():
    assert tags.convert_tags_to_track is media_tags.convert_tags_to_track
