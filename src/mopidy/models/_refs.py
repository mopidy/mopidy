import enum
from typing import ClassVar, Literal, Self

from pydantic.fields import Field

from mopidy.models._base import BaseModel
from mopidy.types import Uri


class ModelType(enum.StrEnum):
    """Enumeration of model types."""

    ALBUM = "album"
    """An album."""

    ARTIST = "artist"
    """An artist."""

    DIRECTORY = "directory"
    """A directory."""

    PLAYLIST = "playlist"
    """A playlist."""

    TRACK = "track"
    """A track."""

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

    uri: Uri
    """The object URI."""

    name: str | None = None
    """The object name."""

    type: ModelType
    """The object type, e.g. "artist", "album", "track", "playlist", "directory"."""

    # For backwards compatibility with Mopidy < 4, we define the `ModelType`
    # enum values as class variables.
    ALBUM: ClassVar[Literal[ModelType.ALBUM]] = ModelType.ALBUM
    ARTIST: ClassVar[Literal[ModelType.ARTIST]] = ModelType.ARTIST
    DIRECTORY: ClassVar[Literal[ModelType.DIRECTORY]] = ModelType.DIRECTORY
    PLAYLIST: ClassVar[Literal[ModelType.PLAYLIST]] = ModelType.PLAYLIST
    TRACK: ClassVar[Literal[ModelType.TRACK]] = ModelType.TRACK

    @classmethod
    def album(cls, *, uri: Uri, name: str | None = None) -> Self:
        """Create a Ref with type [ALBUM][mopidy.models.ModelType.ALBUM]."""
        return cls(uri=uri, name=name, type=ModelType.ALBUM)

    @classmethod
    def artist(cls, *, uri: Uri, name: str | None = None) -> Self:
        """Create a Ref with type [ARTIST][mopidy.models.ModelType.ARTIST]."""
        return cls(uri=uri, name=name, type=ModelType.ARTIST)

    @classmethod
    def directory(cls, *, uri: Uri, name: str | None = None) -> Self:
        """Create a Ref with type [DIRECTORY][mopidy.models.ModelType.DIRECTORY]."""
        return cls(uri=uri, name=name, type=ModelType.DIRECTORY)

    @classmethod
    def playlist(cls, *, uri: Uri, name: str | None = None) -> Self:
        """Create a Ref with type [PLAYLIST][mopidy.models.ModelType.PLAYLIST]."""
        return cls(uri=uri, name=name, type=ModelType.PLAYLIST)

    @classmethod
    def track(cls, *, uri: Uri, name: str | None = None) -> Self:
        """Create a Ref with type [TRACK][mopidy.models.ModelType.TRACK]."""
        return cls(uri=uri, name=name, type=ModelType.TRACK)
