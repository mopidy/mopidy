from __future__ import annotations

import enum
from collections.abc import Iterable
from typing import Literal, NewType, TypeVar

# Date types
Date = NewType("Date", str)
Year = NewType("Year", str)
type DateOrYear = Date | Year


# Integer types
Percentage = NewType("Percentage", int)
DurationMs = NewType("DurationMs", int)


# URI types
Uri = NewType("Uri", str)
UriScheme = NewType("UriScheme", str)


# Query types
F = TypeVar("F")
type QueryValue = str | int
type Query[F] = dict[F, Iterable[QueryValue]]


# Types for distinct queries
type DistinctField = Literal[
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
type SearchField = DistinctField | Literal["any"]
type SearchQuery = dict[SearchField, Iterable[QueryValue]]


# Tracklist types
TracklistId = NewType("TracklistId", int)
type TracklistField = Literal[
    "tlid",
    "uri",
    "name",
    "genre",
    "comment",
    "musicbrainz_id",
]


# Superset of all fields that can be used in a query
type QueryField = DistinctField | SearchField | TracklistField


# Playback types
class PlaybackState(enum.StrEnum):
    """Enum of playback states."""

    #: Constant representing the paused state.
    PAUSED = "paused"

    #: Constant representing the playing state.
    PLAYING = "playing"

    #: Constant representing the stopped state.
    STOPPED = "stopped"
