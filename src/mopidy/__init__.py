import platform
import sys
import warnings
from importlib.metadata import version
from typing import TYPE_CHECKING

if not sys.version_info >= (3, 13):
    sys.exit(
        f"ERROR: Mopidy requires Python >= 3.13, "
        f"but found {platform.python_version()}.",
    )

warnings.filterwarnings("ignore", "could not open display")


# Type checkers see `__version__` as a plain attribute, and do not see
# `__getattr__()`, so that they still report unknown attributes.
if TYPE_CHECKING:
    __version__: str
else:

    def __getattr__(name: str) -> str:
        # `mopidy.__version__` is deprecated since Mopidy 4.1, remove in Mopidy 5.0.
        # Mopidy does not use it itself. Use `mopidy._lib.version.get_version()`
        # internally, and `importlib.metadata.version("mopidy")` outside of Mopidy.
        if name == "__version__":
            warnings.warn(
                "mopidy.__version__ is deprecated since Mopidy 4.1, and will be "
                'removed in Mopidy 5.0. Use importlib.metadata.version("mopidy") '
                "instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            return version("mopidy")
        msg = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(msg)
