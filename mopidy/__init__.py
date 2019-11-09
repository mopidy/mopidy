import platform
import sys
import warnings

if not sys.version_info >= (3, 7):
    sys.exit(
        f"ERROR: Mopidy requires Python >= 3.7, "
        f"but found {platform.python_version()}."
    )


warnings.filterwarnings("ignore", "could not open display")


__version__ = "3.0.0a3"
