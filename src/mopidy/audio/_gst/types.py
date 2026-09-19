from __future__ import annotations

import dataclasses
import enum
from typing import TYPE_CHECKING, Any

from mopidy._lib.gi import Gst
from mopidy.types import PlaybackState

if TYPE_CHECKING:
    from mopidy._lib.gi import GLib


class GstState(enum.Enum):
    """The states a GStreamer element can be in.

    The values are the GStreamer states, so `GstState(gst_state)` converts
    one way and `.value` the other.
    """

    VOID_PENDING = Gst.State.VOID_PENDING
    NULL = Gst.State.NULL
    READY = Gst.State.READY
    PAUSED = Gst.State.PAUSED
    PLAYING = Gst.State.PLAYING

    @property
    def playback_state(self) -> PlaybackState | None:
        """What this state means to Mopidy, if anything.

        READY and VOID_PENDING are GStreamer's own business. They are what
        the pipeline passes through between tracks, and Mopidy has no state
        that says that.
        """
        match self:
            case GstState.NULL:
                return PlaybackState.STOPPED
            case GstState.PAUSED:
                return PlaybackState.PAUSED
            case GstState.PLAYING:
                return PlaybackState.PLAYING
            case _:
                return None


@dataclasses.dataclass(frozen=True)
class GstAsyncDone:
    """An asynchronous state change completed."""


@dataclasses.dataclass(frozen=True)
class GstBuffering:
    """A source reported how full its buffer is."""

    percent: int
    mode: Gst.BufferingMode


@dataclasses.dataclass(frozen=True)
class GstEndOfStream:
    """The pipeline played everything it had."""


@dataclasses.dataclass(frozen=True)
class GstError:
    """An element failed in a way that stops playback."""

    error: GLib.Error
    debug: str


@dataclasses.dataclass(frozen=True)
class GstMissingPlugin:
    """No installed element can handle the media."""

    description: str
    installer_detail: str | None


@dataclasses.dataclass(frozen=True)
class GstStateChanged:
    """The playbin finished, or is part way through, a state change."""

    old_state: GstState
    new_state: GstState
    pending_state: GstState


@dataclasses.dataclass(frozen=True)
class GstStreamStart:
    """A new stream started playing."""


@dataclasses.dataclass(frozen=True)
class GstTag:
    """An element found metadata for what is playing.

    The tags are converted already, so this carries no GStreamer types.
    """

    tags: dict[str, list[Any]]


@dataclasses.dataclass(frozen=True)
class GstWarning:
    """An element reported a problem it could work around."""

    error: GLib.Error
    debug: str


type GstBusMessage = (
    GstAsyncDone
    | GstBuffering
    | GstEndOfStream
    | GstError
    | GstMissingPlugin
    | GstStateChanged
    | GstStreamStart
    | GstTag
    | GstWarning
)
