import enum
from collections.abc import Iterator
from typing import Any, ClassVar, Literal, Self

from pydantic.fields import Field
from pydantic.types import UUID, NonNegativeInt

from mopidy.models._base import BaseModel
from mopidy.types import DateOrYear, DurationMs, TracklistId, Uri

__all__ = [
    "Album",
    "Artist",
    "Image",
    "Playlist",
    "Ref",
    "RefType",
    "SearchResult",
    "TlTrack",
    "Track",
]


class RefType(enum.StrEnum):
    ALBUM = "album"
    ARTIST = "artist"
    DIRECTORY = "directory"
    PLAYLIST = "playlist"
    TRACK = "track"

    def __repr__(self) -> str:
        return self.name


class Ref(BaseModel):
    """Model to represent URI references with a human friendly name and type.

    This is intended for use a lightweight object "free" of metadata
    that can be passed around instead of using full blown models.
    """

    model: Literal["Ref"] = Field(
        default="Ref",
        repr=False,
        alias="__model__",
    )

    #: The object URI. Read-only.
    uri: Uri

    #: The object name. Read-only.
    name: str | None = None

    #: The object type, e.g. "artist", "album", "track", "playlist",
    #: "directory". Read-only.
    type: RefType

    # For backwards compatibility with Mopidy < 4, we define the `RefType` enum
    # values as class variables.
    ALBUM: ClassVar[Literal[RefType.ALBUM]] = RefType.ALBUM
    ARTIST: ClassVar[Literal[RefType.ARTIST]] = RefType.ARTIST
    DIRECTORY: ClassVar[Literal[RefType.DIRECTORY]] = RefType.DIRECTORY
    PLAYLIST: ClassVar[Literal[RefType.PLAYLIST]] = RefType.PLAYLIST
    TRACK: ClassVar[Literal[RefType.TRACK]] = RefType.TRACK

    @classmethod
    def album(cls, *, uri: Uri, name: str | None = None) -> Self:
        """Create a :class:`Ref` with ``type`` :attr:`~RefType.ALBUM`."""
        return cls(uri=uri, name=name, type=RefType.ALBUM)

    @classmethod
    def artist(cls, *, uri: Uri, name: str | None = None) -> Self:
        """Create a :class:`Ref` with ``type`` :attr:`~RefType.ARTIST`."""
        return cls(uri=uri, name=name, type=RefType.ARTIST)

    @classmethod
    def directory(cls, *, uri: Uri, name: str | None = None) -> Self:
        """Create a :class:`Ref` with ``type`` :attr:`~RefType.DIRECTORY`."""
        return cls(uri=uri, name=name, type=RefType.DIRECTORY)

    @classmethod
    def playlist(cls, *, uri: Uri, name: str | None = None) -> Self:
        """Create a :class:`Ref` with ``type`` :attr:`~RefType.PLAYLIST`."""
        return cls(uri=uri, name=name, type=RefType.PLAYLIST)

    @classmethod
    def track(cls, *, uri: Uri, name: str | None = None) -> Self:
        """Create a :class:`Ref` with ``type`` :attr:`~RefType.TRACK`."""
        return cls(uri=uri, name=name, type=RefType.TRACK)


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


class TlTrack(BaseModel):
    """A tracklist track. Wraps a regular track and it's tracklist ID.

    The use of :class:`TlTrack` allows the same track to appear multiple times
    in the tracklist.

    This class also accepts it's parameters as positional arguments. Both
    arguments must be provided, and they must appear in the order they are
    listed here.

    This class also supports iteration, so your extract its values like this::

        (tlid, track) = tl_track
    """

    model: Literal["TlTrack"] = Field(
        default="TlTrack",
        repr=False,
        alias="__model__",
    )

    #: The tracklist ID. Read-only.
    tlid: TracklistId = Field(..., ge=1)

    #: The track. Read-only.
    track: Track

    def __init__(
        self,
        tlid: TracklistId,
        track: Track,
        **_: Any,
    ) -> None:
        super().__init__(tlid=tlid, track=track)  # pyright: ignore[reportCallIssue]

    def __iter__(self) -> Iterator[TracklistId | Track]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return iter((self.tlid, self.track))


class Playlist(BaseModel):
    """A playlist."""

    model: Literal["Playlist"] = Field(
        default="Playlist",
        repr=False,
        alias="__model__",
    )

    #: The playlist URI. Read-only.
    uri: Uri | None = None

    #: The playlist name. Read-only.
    name: str | None = None

    #: The playlist's tracks. Read-only.
    tracks: tuple[Track, ...] = ()

    #: The playlist modification time in milliseconds since Unix epoch.
    #: Read-only.
    last_modified: NonNegativeInt | None = None

    @property
    def length(self) -> NonNegativeInt:
        """The number of tracks in the playlist. Read-only."""
        return len(self.tracks)


class SearchResult(BaseModel):
    """A search result."""

    model: Literal["SearchResult"] = Field(
        default="SearchResult",
        repr=False,
        alias="__model__",
    )

    #: The search result URI. Read-only.
    uri: Uri | None = None

    #: The tracks matching the search query. Read-only.
    tracks: tuple[Track, ...] = ()

    #: The artists matching the search query. Read-only.
    artists: tuple[Artist, ...] = ()

    #: The albums matching the search query. Read-only.
    albums: tuple[Album, ...] = ()
