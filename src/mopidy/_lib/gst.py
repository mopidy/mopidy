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


def millisecond_to_clocktime(value: DurationMs) -> int:
    """Convert a millisecond time to internal GStreamer time."""
    return value * Gst.MSECOND


def clocktime_to_millisecond(value: int) -> DurationMs:
    """Convert an internal GStreamer time to millisecond time."""
    return DurationMs(value // Gst.MSECOND)


def setup_proxy(element: Gst.Element, config: ProxyConfig) -> None:
    """Configure a GStreamer element with proxy settings.

    Args:
        element: Element to setup proxy in.
        config: Proxy settings to use.
    """
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


def repr_tags(tags: dict[str, list[Any]], max_bytes: int = 10) -> str:
    """Returns a printable representation of a `Gst.TagList`.

    Tag values of type bytes are truncated to the specified length to avoid
    large amounts of output when logging.

    Args:
        tags: A converted taglist to be represented.
        max_bytes: The maximum number of bytes to show for bytes tag values.
    """
    result = dict(tags)
    for tag_values in result.values():
        for i, val in enumerate(tag_values):
            if isinstance(val, bytes) and len(val) > max_bytes:
                tag_values[i] = val[:max_bytes] + b"..."
    return repr(result)


def convert_taglist(taglist: Gst.TagList) -> dict[str, list[Any]]:
    """Convert a `Gst.TagList` to plain Python types.

    Knows how to convert:

    - Dates
    - Buffers
    - Numbers
    - Strings
    - Booleans

    Unknown types will be ignored and trace logged. Tag keys are all strings
    defined as part of GStreamer's
    [GstTagList](https://developer.gnome.org/gstreamer/stable/gstreamer-GstTagList.html).

    Args:
        taglist: A GStreamer taglist to be converted.
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
                data = _extract_sample_data(value)
                if data:
                    result[tag].append(data)
            else:
                logger.log(
                    logs.TRACE_LOG_LEVEL,
                    "Ignoring unknown tag data: %r = %r",
                    tag,
                    value,
                )

    # TODO: dict(result) to not leak the defaultdict, or just use setdefault?
    return result


def _extract_sample_data(sample: Gst.Sample) -> bytes | None:
    buf = sample.get_buffer()
    if not buf:
        return None
    return _extract_buffer_data(buf)


# Fix for https://github.com/mopidy/mopidy/issues/1827
# Using GstBuffer.extract_dup() is a memory leak in versions of PyGObject prior
# to v3.36.0. As a workaround we use the GstMemory APIs instead.
def _extract_buffer_data(buf: Gst.Buffer) -> bytes | None:
    mem = buf.get_all_memory()
    if not mem:
        return None
    success, info = mem.map(Gst.MapFlags.READ)
    if not success:
        return None
    if isinstance(info.data, memoryview):  # noqa: SIM108
        # We need to copy the data as the memoryview is released
        # when we call mem.unmap()
        data = bytes(info.data)
    else:
        # GStreamer Python bindings <= 1.16 return a copy of the
        # data as bytes()
        data = info.data
    mem.unmap(info)
    return data
