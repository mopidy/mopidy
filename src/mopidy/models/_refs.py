import enum
from typing import ClassVar, Literal, Self

from pydantic.fields import Field

from mopidy.models._base import BaseModel
from mopidy.types import Uri


class ModelType(enum.StrEnum):
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
    type: ModelType

    # For backwards compatibility with Mopidy < 4, we define the `ModelType`
    # enum values as class variables.
    ALBUM: ClassVar[Literal[ModelType.ALBUM]] = ModelType.ALBUM
    ARTIST: ClassVar[Literal[ModelType.ARTIST]] = ModelType.ARTIST
    DIRECTORY: ClassVar[Literal[ModelType.DIRECTORY]] = ModelType.DIRECTORY
    PLAYLIST: ClassVar[Literal[ModelType.PLAYLIST]] = ModelType.PLAYLIST
    TRACK: ClassVar[Literal[ModelType.TRACK]] = ModelType.TRACK

    @classmethod
    def album(cls, *, uri: Uri, name: str | None = None) -> Self:
        """Create a :class:`Ref` with ``type`` :attr:`~ModelType.ALBUM`."""
        return cls(uri=uri, name=name, type=ModelType.ALBUM)

    @classmethod
    def artist(cls, *, uri: Uri, name: str | None = None) -> Self:
        """Create a :class:`Ref` with ``type`` :attr:`~ModelType.ARTIST`."""
        return cls(uri=uri, name=name, type=ModelType.ARTIST)

    @classmethod
    def directory(cls, *, uri: Uri, name: str | None = None) -> Self:
        """Create a :class:`Ref` with ``type`` :attr:`~ModelType.DIRECTORY`."""
        return cls(uri=uri, name=name, type=ModelType.DIRECTORY)

    @classmethod
    def playlist(cls, *, uri: Uri, name: str | None = None) -> Self:
        """Create a :class:`Ref` with ``type`` :attr:`~ModelType.PLAYLIST`."""
        return cls(uri=uri, name=name, type=ModelType.PLAYLIST)

    @classmethod
    def track(cls, *, uri: Uri, name: str | None = None) -> Self:
        """Create a :class:`Ref` with ``type`` :attr:`~ModelType.TRACK`."""
        return cls(uri=uri, name=name, type=ModelType.TRACK)
