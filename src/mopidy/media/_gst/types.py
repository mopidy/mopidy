from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mopidy._lib.gi import GLib
    from mopidy._lib.gst import GstTags


@dataclasses.dataclass(frozen=True)
class GstAsyncDone:
    """An asynchronous state change completed."""


@dataclasses.dataclass(frozen=True)
class GstDurationChanged:
    """The duration of the media changed."""


@dataclasses.dataclass(frozen=True)
class GstEndOfStream:
    """The pipeline read everything it had."""


@dataclasses.dataclass(frozen=True)
class GstError:
    """An element failed in a way that stops the read."""

    error: GLib.Error
    debug: str | None


@dataclasses.dataclass(frozen=True)
class GstStreamFound:
    """The parsebin exposed a stream of this mime type.

    This is not a GStreamer message type. The reader posts it as an
    application message from the parsebin `pad-added` handler, to move the
    result from the streaming thread to the reader thread.
    """

    mime: str


@dataclasses.dataclass(frozen=True)
class GstMissingPlugin:
    """No installed element can handle the media.

    The mime type is the type of the media that no element can handle, if the
    message tells it.
    """

    mime: str | None


@dataclasses.dataclass(frozen=True)
class GstTag:
    """An element found metadata for the media.

    The tags are converted already, so this carries no GStreamer types.
    """

    tags: GstTags


type GstBusMessage = (
    GstAsyncDone
    | GstDurationChanged
    | GstEndOfStream
    | GstError
    | GstMissingPlugin
    | GstStreamFound
    | GstTag
)
