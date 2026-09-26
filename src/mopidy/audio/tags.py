"""The deprecated tag helpers.

These convert GStreamer taglists, so they moved in with the rest of the
GStreamer code. A scanner returns a [Track][mopidy.models.Track] in its
[ScanResult][mopidy.audio.ScanResult] now, which is what callers converted
the tags to.
"""

from typing import Any
from warnings import deprecated

from mopidy._lib.gi import Gst
from mopidy.audio._gst import tags as gst_tags
from mopidy.models import Track
from mopidy.types import DurationMs, Uri


@deprecated(
    "mopidy.audio.tags.repr_tags() is deprecated since Mopidy 4.1 and will be "
    "removed in Mopidy 5.0. It represents a GStreamer taglist, so it is not "
    "part of the audio API. There is no public replacement."
)
def repr_tags(tags: dict[str, list[Any]], max_bytes: int = 10) -> str:
    """Returns a printable representation of a `Gst.TagList`.

    !!! warning "Deprecated since Mopidy 4.1"

        Removed in Mopidy 5.0, with no public replacement.

    Args:
        tags: A converted taglist to be represented.
        max_bytes: The maximum number of bytes to show for bytes tag values.
    """
    return gst_tags.repr_tags(tags, max_bytes)


@deprecated(
    "mopidy.audio.tags.convert_taglist() is deprecated since Mopidy 4.1 and "
    "will be removed in Mopidy 5.0. It takes a GStreamer taglist, so it is "
    "not part of the audio API. There is no public replacement."
)
def convert_taglist(taglist: Gst.TagList) -> dict[str, list[Any]]:
    """Convert a `Gst.TagList` to plain Python types.

    !!! warning "Deprecated since Mopidy 4.1"

        Removed in Mopidy 5.0, with no public replacement.

    Args:
        taglist: A GStreamer taglist to be converted.
    """
    return gst_tags.convert_taglist(taglist)


@deprecated(
    "mopidy.audio.tags.convert_tags_to_track() is deprecated since Mopidy 4.1 "
    "and will be removed in Mopidy 5.0. Scanners build the track themselves: "
    "read it off the mopidy.audio.ScanResult instead."
)
def convert_tags_to_track(
    tags: dict[str, Any],
    *,
    uri: Uri,
    length: DurationMs | None = None,
    last_modified: int | None = None,
) -> Track:
    """Convert our normalized tags to a track.

    !!! warning "Deprecated since Mopidy 4.1"

        Read the track off the [ScanResult][mopidy.audio.ScanResult] that
        [Scanner.scan()][mopidy.audio.Scanner.scan] returns. Removed in
        Mopidy 5.0.

    Raises:
        exceptions.ScannerError: If the tags can't be coerced into a valid
            `Track`.
    """
    return gst_tags.convert_tags_to_track(
        tags,
        uri=uri,
        length=length,
        last_modified=last_modified,
    )
