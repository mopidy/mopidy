from typing import Literal
from uuid import UUID

from pydantic.fields import Field
from pydantic.types import NonNegativeInt

from mopidy.models._base import BaseModel
from mopidy.types import DateOrYear, DurationMs, Uri


class Image(BaseModel):
    """An image with a URI and dimensions."""

    model: Literal["Image"] = Field(
        default="Image",
        repr=False,
        alias="__model__",
    )

    uri: Uri
    """The image URI."""

    width: NonNegativeInt | None = None
    """Width of the image in pixels."""

    height: NonNegativeInt | None = None
    """Height of the image in pixels."""


class Artist(BaseModel):
    """An artist."""

    model: Literal["Artist"] = Field(
        default="Artist",
        repr=False,
        alias="__model__",
    )

    uri: Uri | None = None
    """The artist URI."""

    name: str | None = None
    """The artist name."""

    sortname: str | None = None
    """Artist name for better sorting, e.g. with articles stripped."""

    musicbrainz_id: UUID | None = None
    """The MusicBrainz ID of the artist."""


class Album(BaseModel):
    """An album."""

    model: Literal["Album"] = Field(
        default="Album",
        repr=False,
        alias="__model__",
    )

    uri: Uri | None = None
    """The album URI."""

    name: str | None = None
    """The album name."""

    artists: frozenset[Artist] = frozenset()
    """A set of album artists."""

    num_tracks: NonNegativeInt | None = None
    """The number of tracks in the album."""

    num_discs: NonNegativeInt | None = None
    """The number of discs in the album."""

    date: DateOrYear | None = Field(
        default=None,
        pattern=r"^\d{4}(-\d{2}-\d{2})?$",
    )
    """The album release date. A string formatted as "YYYY" or "YYYY-MM-DD"."""

    musicbrainz_id: UUID | None = None
    """The MusicBrainz ID of the album."""


class Track(BaseModel):
    """An audio track."""

    model: Literal["Track"] = Field(
        default="Track",
        repr=False,
        alias="__model__",
    )

    uri: Uri
    """The track URI."""

    name: str | None = None
    """The track name."""

    artists: frozenset[Artist] = frozenset()
    """A set of track artists."""

    album: Album | None = None
    """The track album."""

    composers: frozenset[Artist] = frozenset()
    """A set of track composers."""

    performers: frozenset[Artist] = frozenset()
    """A set of track performers."""

    genre: str | None = None
    """The track genre."""

    track_no: NonNegativeInt | None = None
    """The track number in the album."""

    disc_no: NonNegativeInt | None = None
    """The disc number in the album."""

    date: DateOrYear | None = Field(
        default=None,
        pattern=r"^\d{4}(-\d{2}-\d{2})?$",
    )
    """The track release date. A string formatted as "YYYY" or "YYYY-MM-DD"."""

    length: DurationMs | None = None
    """The track length in milliseconds."""

    bitrate: NonNegativeInt | None = None
    """The track's bitrate in kbit/s."""

    comment: str | None = None
    """The track comment."""

    musicbrainz_id: UUID | None = None
    """The MusicBrainz ID of the track."""

    last_modified: NonNegativeInt | None = None
    """
    Integer representing when the track was last modified.

    Exact meaning depends on source of track. For local files this is the
    modification time in milliseconds since Unix epoch. For other backends
    it could be an equivalent timestamp or simply a version counter.
    """
