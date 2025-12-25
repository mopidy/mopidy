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

    #: The image URI. Read-only.
    uri: Uri

    #: Optional width of the image or :class:`None`. Read-only.
    width: NonNegativeInt | None = None

    #: Optional height of the image or :class:`None`. Read-only.
    height: NonNegativeInt | None = None


class Artist(BaseModel):
    """An artist."""

    model: Literal["Artist"] = Field(
        default="Artist",
        repr=False,
        alias="__model__",
    )

    #: The artist URI. Read-only.
    uri: Uri | None = None

    #: The artist name. Read-only.
    name: str | None = None

    #: Artist name for better sorting, e.g. with articles stripped. Read only.
    sortname: str | None = None

    #: The MusicBrainz ID of the artist. Read-only.
    musicbrainz_id: UUID | None = None


class Album(BaseModel):
    """An album."""

    model: Literal["Album"] = Field(
        default="Album",
        repr=False,
        alias="__model__",
    )

    #: The album URI. Read-only.
    uri: Uri | None = None

    #: The album name. Read-only.
    name: str | None = None

    #: A set of album artists. Read-only.
    artists: frozenset[Artist] = frozenset()

    #: The number of tracks in the album. Read-only.
    num_tracks: NonNegativeInt | None = None

    #: The number of discs in the album. Read-only.
    num_discs: NonNegativeInt | None = None

    #: The album release date. Read-only.
    date: DateOrYear | None = Field(
        default=None,
        pattern=r"^\d{4}(-\d{2}-\d{2})?$",
    )

    #: The MusicBrainz ID of the album. Read-only.
    musicbrainz_id: UUID | None = None


class Track(BaseModel):
    """A track."""

    model: Literal["Track"] = Field(
        default="Track",
        repr=False,
        alias="__model__",
    )

    #: The track URI. Read-only.
    uri: Uri | None = None

    #: The track name. Read-only.
    name: str | None = None

    #: A set of track artists. Read-only.
    artists: frozenset[Artist] = frozenset()

    #: The track :class:`Album`. Read-only.
    album: Album | None = None

    #: A set of track composers. Read-only.
    composers: frozenset[Artist] = frozenset()

    #: A set of track performers. Read-only.
    performers: frozenset[Artist] = frozenset()

    #: The track genre. Read-only.
    genre: str | None = None

    #: The track number in the album. Read-only.
    track_no: NonNegativeInt | None = None

    #: The disc number in the album. Read-only.
    disc_no: NonNegativeInt | None = None

    #: The track release date. Read-only.
    date: DateOrYear | None = Field(
        default=None,
        pattern=r"^\d{4}(-\d{2}-\d{2})?$",
    )

    #: The track length in milliseconds or :class:`None` if there is no duration.
    #: Read-only.
    length: DurationMs | None = None

    #: The track's bitrate in kbit/s. Read-only.
    bitrate: NonNegativeInt | None = None

    #: The track comment. Read-only.
    comment: str | None = None

    #: The MusicBrainz ID of the track. Read-only.
    musicbrainz_id: UUID | None = None

    #: Integer representing when the track was last modified. Exact meaning
    #: depends on source of track. For local files this is the modification
    #: time in milliseconds since Unix epoch. For other backends it could be an
    #: equivalent timestamp or simply a version counter.
    last_modified: NonNegativeInt | None = None
