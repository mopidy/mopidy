import platform
import sys
import warnings
from importlib.metadata import version

if not sys.version_info >= (3, 13):
    sys.exit(
        f"ERROR: Mopidy requires Python >= 3.13, "
        f"but found {platform.python_version()}.",
    )

warnings.filterwarnings("ignore", "could not open display")

# Deprecated since Mopidy 4.1, remove in Mopidy 5.0. Mopidy does not use this
# itself. Use `mopidy._lib.version.get_version()` internally, and
# `importlib.metadata.version("mopidy")` outside of Mopidy.
__version__ = version("mopidy")
