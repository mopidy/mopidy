import platform
import sys
import warnings
from importlib.metadata import version

if not sys.version_info >= (3, 11):
    sys.exit(
        f"ERROR: Mopidy requires Python >= 3.11, "
        f"but found {platform.python_version()}.",
    )

warnings.filterwarnings("ignore", "could not open display")

__version__ = version("mopidy")
