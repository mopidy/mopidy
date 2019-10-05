from __future__ import absolute_import, print_function, unicode_literals

import os
import platform
import posixpath
import sys
import warnings


if not (2, 7) <= sys.version_info < (3,):
    sys.exit(
        'ERROR: Mopidy requires Python 2.7, but found %s.' %
        platform.python_version())


warnings.filterwarnings('ignore', 'could not open display')


__version__ = '2.3.0'


def posix_normpath(*paths):
    """if path has win32 backslashes, convert to forward slashes"""
    res = paths[0].split(os.path.sep)
    for path in paths[1:]:
        path_parts = path.split(os.path.sep)
        res.extend(path_parts)
    return posixpath.sep.join(res)
