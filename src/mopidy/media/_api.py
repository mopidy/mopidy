from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from mopidy.exceptions import MopidyException

if TYPE_CHECKING:
    from mopidy.media._models import MediaInfo
    from mopidy.types import DurationMs, Uri


class MediaReadError(MopidyException):
    """Raised when a URI cannot be read, or when a read times out."""


class MediaInfoReader(Protocol):
    """The part of a reader that a media framework implements."""

    def read_media_info(self, uri: Uri, *, timeout: DurationMs) -> MediaInfo:
        """Read the media info of one URI.

        Raises:
            MediaReadError: If the URI cannot be read, or on a timeout.
        """
        ...
