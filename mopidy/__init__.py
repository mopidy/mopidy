from __future__ import absolute_import, print_function, unicode_literals

import platform
import sys
import warnings


compatible_py2 = (2, 7) <= sys.version_info < (3,)
compatible_py3 = (3, 7) <= sys.version_info

if not (compatible_py2 or compatible_py3):
    sys.exit(
        'ERROR: Mopidy requires Python 2.7 or >=3.7, but found %s.' %
        platform.python_version())


warnings.filterwarnings('ignore', 'could not open display')


__version__ = '3.0.0a1'
