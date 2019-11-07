from __future__ import absolute_import, print_function, unicode_literals

import platform
import sys
import warnings


if not sys.version_info >= (3, 7):
    sys.exit(
        "ERROR: Mopidy requires Python >= 3.7, but found %s."
        % platform.python_version()
    )


warnings.filterwarnings("ignore", "could not open display")


__version__ = "3.0.0a2"
