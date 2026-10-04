"""The deprecated tag helpers.

Use
[MediaReader.read_media_info()][mopidy.media.MediaReader.read_media_info] instead. They
give the metadata as a [Track][mopidy.models.Track], and the embedded
images as bytes.
"""

from typing import Any
from warnings import deprecated

from mopidy._lib import gst
from mopidy._lib.gi import Gst
from mopidy.media._gst import tags as media_tags
from mopidy.models import Track
from mopidy.types import DurationMs, Uri


@deprecated(
    "mopidy.audio.tags.repr_tags() is deprecated since Mopidy 4.1, and will "
    "be removed in Mopidy 5.0. Use mopidy.media.MediaReader.read_media_info() "
    "instead."
)
def repr_tags(tags: dict[str, list[Any]], max_bytes: int = 10) -> str:
    """Returns a printable representation of a `Gst.TagList`.

    /// warning | Deprecated
    Deprecated since Mopidy 4.1, and will be removed in Mopidy 5.0. Use
    [MediaReader.read_media_info()][mopidy.media.MediaReader.read_media_info] instead.
    ///

    Args:
        tags: A converted taglist to be represented.
        max_bytes: The maximum number of bytes to show for bytes tag values.
    """
    return gst.repr_tags(tags, max_bytes)


@deprecated(
    "mopidy.audio.tags.convert_taglist() is deprecated since Mopidy 4.1, "
    "and will be removed in Mopidy 5.0. Use "
    "mopidy.media.MediaReader.read_media_info() instead."
)
def convert_taglist(taglist: Gst.TagList) -> dict[str, list[Any]]:
    """Convert a `Gst.TagList` to plain Python types.

    /// warning | Deprecated
    Deprecated since Mopidy 4.1, and will be removed in Mopidy 5.0. Use
    [MediaReader.read_media_info()][mopidy.media.MediaReader.read_media_info] instead.
    ///

    Args:
        taglist: A GStreamer taglist to be converted.
    """
    return gst.convert_taglist(taglist)


@deprecated(
    "mopidy.audio.tags.convert_tags_to_track() is deprecated since Mopidy "
    "4.1, and will be removed in Mopidy 5.0. Use "
    "mopidy.media.MediaReader.read_media_info() instead. The track is in "
    "MediaInfo.track."
)
def convert_tags_to_track(
    tags: dict[str, Any],
    *,
    uri: Uri,
    length: DurationMs | None = None,
    last_modified: int | None = None,
) -> Track:
    """Convert our normalized tags to a track.

    /// warning | Deprecated
    Deprecated since Mopidy 4.1, and will be removed in Mopidy 5.0. Use
    [MediaReader.read_media_info()][mopidy.media.MediaReader.read_media_info] instead.
    The track is in [MediaInfo.track][mopidy.media.MediaInfo.track].
    ///

    Raises:
        exceptions.ScannerError: If the tags can't be coerced into a valid
            `Track`.
    """
    return media_tags.convert_tags_to_track(
        tags,
        uri=uri,
        length=length,
        last_modified=last_modified,
    )
