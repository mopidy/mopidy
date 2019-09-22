from __future__ import absolute_import, print_function, unicode_literals

import platform
import sys
import warnings
import os, posixpath


if not (2, 7) <= sys.version_info < (3,):
    sys.exit(
        'ERROR: Mopidy requires Python 2.7, but found %s.' %
        platform.python_version())


warnings.filterwarnings('ignore', 'could not open display')


__version__ = '3.0.0a1'


def posix_normpath(path, keep_drive=False):
    """if path has win32 backslashes, convert to forward slashes"""
    drive, path = os.path.splitdrive(path)
    path_parts = path.split(os.path.sep)
    if drive and keep_drive:
        path_parts[0] = drive
    return posixpath.sep.join(path_parts)
