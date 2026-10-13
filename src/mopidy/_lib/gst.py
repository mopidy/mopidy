from __future__ import annotations

import collections
import datetime as dt
import logging
import numbers
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from mopidy import httpclient
from mopidy._lib import logs
from mopidy._lib.gi import GLib, Gst
from mopidy.types import DurationMs

if TYPE_CHECKING:
    from mopidy.config import ProxyConfig

logger = logging.getLogger(__name__)


def to_gst_time(duration: DurationMs) -> int:
    """Convert a duration to GStreamer time, which is in nanoseconds."""
    return duration * Gst.MSECOND


def from_gst_time(gst_time: int) -> DurationMs:
    """Convert GStreamer time, which is in nanoseconds, to a duration."""
    return DurationMs(gst_time // Gst.MSECOND)


type GstTags = dict[str, list[Any]]
"""Tags converted to plain Python types, by tag name."""


def from_gst_taglist(taglist: Gst.TagList) -> GstTags:
    """Convert a `Gst.TagList` to plain Python types.

    The keys are the GStreamer tag names, see
    [GstTagList](https://gstreamer.freedesktop.org/documentation/gstreamer/gsttaglist.html).
    Each value is a list, as a tag can have more than one value. The values
    are converted like this:

    - Dates and date-times become ISO 8601 strings.
    - Samples, such as embedded images, become bytes.
    - Bytes become strings.
    - Strings, booleans, and numbers do not change.

    Dates that are not valid, and values of other types, are left out and
    logged.
    """
    result = collections.defaultdict(list)

    for n in range(taglist.n_tags()):
        tag = taglist.nth_tag_name(n)

        for i in range(taglist.get_tag_size(tag)):
            value = taglist.get_value_index(tag, i)

            if isinstance(value, GLib.Date):
                try:
                    date = dt.date(
                        value.get_year(),
                        value.get_month(),
                        value.get_day(),
                    )
                    result[tag].append(date.isoformat())
                except ValueError:
                    logger.debug(
                        "Ignoring dodgy date value: %d-%d-%d",
                        value.get_year(),
                        value.get_month(),
                        value.get_day(),
                    )
            elif isinstance(value, Gst.DateTime):
                result[tag].append(value.to_iso8601_string())
            elif isinstance(value, bytes):
                result[tag].append(value.decode(errors="replace"))
            elif isinstance(value, str | bool | numbers.Number):
                result[tag].append(value)
            elif isinstance(value, Gst.Sample):
                if (buf := value.get_buffer()) and (
                    data := buf.extract_dup(0, buf.get_size())
                ):
                    result[tag].append(data)
            else:
                logger.log(
                    logs.TRACE_LOG_LEVEL,
                    "Ignoring unknown tag data: %r = %r",
                    tag,
                    value,
                )

    return dict(result)


def repr_tags(tags: GstTags, max_bytes: int = 10) -> str:
    """Return a printable representation of tags from `from_gst_taglist()`.

    Bytes values are cut to `max_bytes`, so that embedded images do not fill
    the log.
    """
    return repr(
        {
            tag: [
                value[:max_bytes] + b"..."
                if isinstance(value, bytes) and len(value) > max_bytes
                else value
                for value in values
            ]
            for tag, values in tags.items()
        }
    )


def setup_proxy(element: Gst.Element, config: ProxyConfig) -> None:
    """Configure a GStreamer element with proxy settings."""
    if not hasattr(element.props, "proxy") or not config.get("hostname"):
        return

    element.set_property("proxy", httpclient.format_proxy(config, auth=False))
    element.set_property("proxy-id", config.get("username"))
    element.set_property("proxy-pw", config.get("password"))


class Signals:
    """Helper for tracking gobject signal registrations."""

    def __init__(self) -> None:
        self._ids: dict[tuple[Gst.Element, str], int] = {}

    def connect(
        self,
        element: Gst.Element,
        event: str,
        func: Callable,
        *args: Any,
    ) -> None:
        """Connect a function + args to signal event on an element.

        Each event may only be handled by one callback in this implementation.
        """
        if (element, event) in self._ids:
            raise AssertionError
        self._ids[(element, event)] = element.connect(event, func, *args)

    def disconnect(self, element: Gst.Element, event: str) -> None:
        """Disconnect whatever handler we have for an element+event pair.

        Does nothing it the handler has already been removed.
        """
        signal_id = self._ids.pop((element, event), None)
        if signal_id is not None:
            element.disconnect(signal_id)

    def clear(self) -> None:
        """Clear all registered signal handlers."""
        for element, event in list(self._ids):
            element.disconnect(self._ids.pop((element, event)))
