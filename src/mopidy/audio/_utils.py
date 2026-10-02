from __future__ import annotations

from typing import TYPE_CHECKING, cast

from mopidy._lib.gi import Gst
from mopidy.types import UriScheme

if TYPE_CHECKING:
    from collections.abc import Iterable


def supported_uri_schemes(uri_schemes: Iterable[UriScheme]) -> set[UriScheme]:
    """Determine which URIs we can actually support from provided whitelist.

    Args:
        uri_schemes: List/set of URIs to check support for.
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
