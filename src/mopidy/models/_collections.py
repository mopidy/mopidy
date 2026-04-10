from typing import Literal

from pydantic.fields import Field
from pydantic.types import NonNegativeInt

from mopidy.models._base import BaseModel
from mopidy.models._models import Album, Artist, Track
from mopidy.types import Uri


class Playlist(BaseModel):
    """A playlist."""

    model: Literal["Playlist"] = Field(
        default="Playlist",
        repr=False,
        alias="__model__",
    )

    uri: Uri
    """The playlist URI."""

    name: str | None = None
    """The playlist name."""

    tracks: tuple[Track, ...] = ()
    """The playlist's tracks."""

    last_modified: NonNegativeInt | None = None
    """The playlist modification time in milliseconds since Unix epoch."""

    @property
    def length(self) -> NonNegativeInt:
        """The number of tracks in the playlist."""
        return len(self.tracks)


class SearchResult(BaseModel):
    """A search result."""

    model: Literal["SearchResult"] = Field(
        default="SearchResult",
        repr=False,
        alias="__model__",
    )

    uri: Uri | None = None
    """The search result URI."""

    tracks: tuple[Track, ...] = ()
    """The tracks matching the search query."""

    artists: tuple[Artist, ...] = ()
    """The artists matching the search query."""

    albums: tuple[Album, ...] = ()
    """The albums matching the search query."""
