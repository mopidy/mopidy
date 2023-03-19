import platform
import sys
import warnings

import pkg_resources

if not sys.version_info >= (3, 9):
    sys.exit(
        f"ERROR: Mopidy requires Python >= 3.9, "
        f"but found {platform.python_version()}."
    )

warnings.filterwarnings("ignore", "could not open display")

__version__ = pkg_resources.get_distribution("Mopidy").version
