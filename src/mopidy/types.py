from __future__ import annotations

import enum
from collections.abc import Iterable
from typing import TYPE_CHECKING, Literal, NewType, TypeVar

if TYPE_CHECKING:
    from typing import TypeAlias


# Date types
Date = NewType("Date", str)
Year = NewType("Year", str)
DateOrYear = Date | Year


# Integer types
Percentage = NewType("Percentage", int)
DurationMs = NewType("DurationMs", int)


# URI types
Uri = NewType("Uri", str)
UriScheme = NewType("UriScheme", str)


# Query types
F = TypeVar("F")
QueryValue: TypeAlias = str | int
Query: TypeAlias = dict[F, Iterable[QueryValue]]


# Types for distinct queries
DistinctField: TypeAlias = Literal[
    "uri",
    "track_name",
    "album",
    "artist",
    "albumartist",
    "composer",
    "performer",
    "track_no",
    "genre",
    "date",
    "comment",
    "disc_no",
    "musicbrainz_albumid",
    "musicbrainz_artistid",
    "musicbrainz_trackid",
]


# Types for search queries
SearchField: TypeAlias = DistinctField | Literal["any"]
SearchQuery: TypeAlias = dict[SearchField, Iterable[QueryValue]]


# Tracklist types
TracklistId = NewType("TracklistId", int)
TracklistField: TypeAlias = Literal[
    "tlid",
    "uri",
    "name",
    "genre",
    "comment",
    "musicbrainz_id",
]


# Superset of all fields that can be used in a query
QueryField: TypeAlias = DistinctField | SearchField | TracklistField


# Playback types
class PlaybackState(enum.StrEnum):
    """Enum of playback states."""

    #: Constant representing the paused state.
    PAUSED = "paused"

    #: Constant representing the playing state.
    PLAYING = "playing"

    #: Constant representing the stopped state.
    STOPPED = "stopped"
