from collections.abc import Iterable

from mopidy.types import UriScheme


def supported_uri_schemes(uri_schemes: Iterable[UriScheme]) -> set[UriScheme]:
    return set(uri_schemes)  # We pretend to support all of these.
