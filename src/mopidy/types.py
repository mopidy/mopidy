from __future__ import annotations

import enum
from collections.abc import Iterable
from typing import Literal, NewType, TypeVar

# Date types
Date = NewType("Date", str)
"""A date string on the form ``YYYY-MM-DD``."""

Year = NewType("Year", str)
"""A year string on the form ``YYYY``."""

type DateOrYear = Date | Year
"""A :class:`Date` or :class:`Year`."""


# Integer types
Percentage = NewType("Percentage", int)
"""An integer in the range 0–100 representing a percentage."""

DurationMs = NewType("DurationMs", int)
"""A duration in milliseconds."""


# URI types
Uri = NewType("Uri", str)
"""A URI string identifying a resource, e.g. a track or stream."""

UriScheme = NewType("UriScheme", str)
"""The scheme part of a URI, e.g. ``spotify`` or ``file``."""


# Query types
F = TypeVar("F")
type QueryValue = str | int
"""A single query value; either a string or an integer."""

type Query[F] = dict[F, Iterable[QueryValue]]
"""A query mapping field names to lists of :class:`QueryValue`."""


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
"""A field name that can be used in a :meth:`~mopidy.core.LibraryController.get_distinct` query."""


# Types for search queries
type SearchField = DistinctField | Literal["any"]
"""A field name that can be used in a :meth:`~mopidy.core.LibraryController.search` query."""

type SearchQuery = dict[SearchField, Iterable[QueryValue]]
"""A search query mapping :class:`SearchField` names to lists of :class:`QueryValue`."""


# Tracklist types
TracklistId = NewType("TracklistId", int)
"""A unique integer ID for a tracklist item."""

type TracklistField = Literal[
    "tlid",
    "uri",
    "name",
    "genre",
    "comment",
    "musicbrainz_id",
]
"""A field name that can be used in a tracklist query."""


# Superset of all fields that can be used in a query
type QueryField = DistinctField | SearchField | TracklistField
"""A superset of all field names that can be used in any query."""


# Playback types
class PlaybackState(enum.StrEnum):
    """Enum of playback states."""

    PAUSED = "paused"
    """Constant representing the paused state."""

    PLAYING = "playing"
    """Constant representing the playing state."""

    STOPPED = "stopped"
    """Constant representing the stopped state."""
