from functools import cache
from importlib.metadata import version


@cache
def get_version() -> str:
    """Get the version of the installed Mopidy distribution."""
    return version("mopidy")
