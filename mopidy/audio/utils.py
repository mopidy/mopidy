from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, cast

from mopidy import httpclient
from mopidy.internal.gi import Gst
from mopidy.types import DurationMs, UriScheme

if TYPE_CHECKING:
    from collections.abc import Iterable

    from mopidy.config import ProxyConfig


def millisecond_to_clocktime(value: DurationMs) -> int:
    """Convert a millisecond time to internal GStreamer time."""
    return value * Gst.MSECOND


def clocktime_to_millisecond(value: int) -> DurationMs:
    """Convert an internal GStreamer time to millisecond time."""
    return DurationMs(value // Gst.MSECOND)


def supported_uri_schemes(uri_schemes: Iterable[UriScheme]) -> set[UriScheme]:
    """Determine which URIs we can actually support from provided whitelist.

    :param uri_schemes: list/set of URIs to check support for.
    :type uri_schemes: list or set or URI schemes as strings.
    :rtype: set of URI schemes we can support via this GStreamer install.
    """
    supported_schemes = set()
    registry = Gst.Registry.get()

    for factory in registry.get_feature_list(Gst.ElementFactory):
        factory = cast(Gst.ElementFactory, factory)
        for uri_protocol in factory.get_uri_protocols():
            uri_scheme = UriScheme(uri_protocol)
            if uri_scheme in uri_schemes:
                supported_schemes.add(uri_scheme)

    return supported_schemes


def setup_proxy(element: Gst.Element, config: ProxyConfig) -> None:
    """Configure a GStreamer element with proxy settings.

    :param element: element to setup proxy in.
    :type element: :class:`Gst.GstElement`
    :param config: proxy settings to use.
    :type config: :class:`dict`
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
