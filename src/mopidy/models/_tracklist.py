from collections.abc import Iterator
from typing import Any, Literal

from pydantic.fields import Field

from mopidy.models._base import BaseModel
from mopidy.models._models import Track
from mopidy.types import TracklistId


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
        super().__init__(tlid=tlid, track=track)  # pyright: ignore[reportCallIssue]  # ty:ignore[unknown-argument]

    def __iter__(self) -> Iterator[TracklistId | Track]:  # pyright: ignore[reportIncompatibleMethodOverride]  # ty:ignore[invalid-method-override]
        return iter((self.tlid, self.track))
