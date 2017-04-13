from __future__ import absolute_import, print_function, unicode_literals

import platform
import sys
import warnings


if not (2, 7) <= sys.version_info < (3,):
    sys.exit(
        'ERROR: Mopidy requires Python 2.7, but found %s.' %
        platform.python_version())


warnings.filterwarnings('ignore', 'could not open display')


__version__ = '2.1.0'
