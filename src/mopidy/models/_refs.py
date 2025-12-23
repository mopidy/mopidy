import enum
from typing import ClassVar, Literal, Self

from pydantic.fields import Field

from mopidy.models._base import BaseModel
from mopidy.types import Uri


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
