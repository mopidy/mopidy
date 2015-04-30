from __future__ import absolute_import, print_function, unicode_literals

import platform
import sys
import textwrap
import warnings


if not (2, 7) <= sys.version_info < (3,):
    sys.exit(
        'ERROR: Mopidy requires Python 2.7, but found %s.' %
        platform.python_version())

try:
    import gobject   # noqa
except ImportError:
    print(textwrap.dedent("""
        ERROR: The gobject Python package was not found.

        Mopidy requires GStreamer (and GObject) to work. These are C libraries
        with a number of dependencies themselves, and cannot be installed with
        the regular Python tools like pip.

        Please see http://docs.mopidy.com/en/latest/installation/ for
        instructions on how to install the required dependencies.
    """))
    raise


warnings.filterwarnings('ignore', 'could not open display')


__version__ = '1.0.4'
