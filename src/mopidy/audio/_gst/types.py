from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mopidy._lib.gi import GLib, Gst


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

    old_state: Gst.State
    new_state: Gst.State
    pending_state: Gst.State


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
