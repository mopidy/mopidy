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
