from typing import Self

import pydantic

from mopidy.models import Track
from mopidy.models._base import BaseModel
from mopidy.types import Uri


class EmbeddedImage(BaseModel):
    """An image that is embedded in media, such as cover art."""

    data: bytes
    """The image data."""


class MediaInfo(BaseModel):
    """The media info of one URI."""

    track: Track
    """The metadata as a track.

    `track.uri` is the URI that was read. `track.length` is the duration, or
    `None` if the duration is not known.
    """

    playable: bool
    """If the media info reader decoded audio.

    This does not tell if the playback engine can play the URI.
    """

    seekable: bool
    """If the media allows seeking."""

    images: tuple[EmbeddedImage, ...] = ()
    """The images that are embedded in the media."""


class PlaylistEntry(BaseModel):
    """One entry in a playlist document."""

    track: Track
    """The metadata of the entry as a track.

    `track.uri` is the first alternative. `track.name` and `track.length` are
    set if the playlist document has them.
    """

    alternatives: tuple[Uri, ...]
    """The URIs of the entry, in the order of the playlist document.

    There is at least one alternative.
    """

    @pydantic.model_validator(mode="after")
    def _check_alternatives(self) -> Self:
        if not self.alternatives:
            msg = "A playlist entry must have at least one alternative."
            raise ValueError(msg)
        if self.track.uri != self.alternatives[0]:
            msg = "The track URI must be the first alternative."
            raise ValueError(msg)
        return self


class PlaybackTarget(BaseModel):
    """The URI to give to the playback engine, found from another URI."""

    uri: Uri
    """The URI to play."""

    info: MediaInfo | None
    """The media info of the URI.

    `None` if the URI could not be read, but is not a playlist document. Then
    the playback target is not verified, and the playback engine can still try
    to play it.
    """

    entry: PlaylistEntry | None
    """The playlist entry that the URI came from.

    This is the entry in the last playlist document, or `None` if the first URI
    was the playback target.
    """
