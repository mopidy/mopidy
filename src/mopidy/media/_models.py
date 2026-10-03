from mopidy.models import Track
from mopidy.models._base import BaseModel


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
