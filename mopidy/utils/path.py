from __future__ import unicode_literals

import logging
import os
import re
# pylint: disable = W0402
import string
# pylint: enable = W0402
import sys
import urllib

import glib

logger = logging.getLogger('mopidy.utils.path')

XDG_CACHE_DIR = glib.get_user_cache_dir().decode('utf-8')
XDG_CONFIG_DIR = glib.get_user_config_dir().decode('utf-8')
XDG_DATA_DIR = glib.get_user_data_dir().decode('utf-8')
XDG_MUSIC_DIR = glib.get_user_special_dir(glib.USER_DIRECTORY_MUSIC)
if XDG_MUSIC_DIR:
    XDG_MUSIC_DIR = XDG_MUSIC_DIR.decode('utf-8')
XDG_DIRS = {
    'XDG_CACHE_DIR': XDG_CACHE_DIR,
    'XDG_CONFIG_DIR': XDG_CONFIG_DIR,
    'XDG_DATA_DIR': XDG_DATA_DIR,
    'XDG_MUSIC_DIR': XDG_MUSIC_DIR,
}


def get_or_create_dir(dir_path):
    dir_path = expand_path(dir_path)
    if os.path.isfile(dir_path):
        raise OSError(
            'A file with the same name as the desired dir, '
            '"%s", already exists.' % dir_path)
    elif not os.path.isdir(dir_path):
        logger.info('Creating dir %s', dir_path)
        os.makedirs(dir_path, 0755)
    return dir_path


def get_or_create_file(file_path):
    file_path = expand_path(file_path)
    get_or_create_dir(os.path.dirname(file_path))
    if not os.path.isfile(file_path):
        logger.info('Creating file %s', file_path)
        open(file_path, 'w').close()
    return file_path


def path_to_uri(*paths):
    """
    Convert OS specific path to file:// URI.

    Accepts either unicode strings or bytestrings. The encoding of any
    bytestring will be maintained so that :func:`uri_to_path` can return the
    same bytestring.

    Returns a file:// URI as an unicode string.
    """
    path = os.path.join(*paths)
    if isinstance(path, unicode):
        path = path.encode('utf-8')
    if sys.platform == 'win32':
        return 'file:' + urllib.quote(path)
    return 'file://' + urllib.quote(path)


def uri_to_path(uri):
    """
    Convert the file:// to a OS specific path.

    Returns a bytestring, since the file path can contain chars with other
    encoding than UTF-8.

    If we had returned these paths as unicode strings, you wouldn't be able to
    look up the matching dir or file on your file system because the exact path
    would be lost by ignoring its encoding.
    """
    if isinstance(uri, unicode):
        uri = uri.encode('utf-8')
    if sys.platform == 'win32':
        return urllib.unquote(re.sub(b'^file:', b'', uri))
    else:
        return urllib.unquote(re.sub(b'^file://', b'', uri))


def split_path(path):
    parts = []
    while True:
        path, part = os.path.split(path)
        if part:
            parts.insert(0, part)
        if not path or path == b'/':
            break
    return parts


def expand_path(path):
    # TODO: expandvars as well?
    path = string.Template(path).safe_substitute(XDG_DIRS)
    path = os.path.expanduser(path)
    path = os.path.abspath(path)
    return path


def find_files(path):
    """
    Finds all files within a path.

    Directories and files with names starting with ``.`` is ignored.

    :returns: yields the full path to files as bytestrings
    """
    if isinstance(path, unicode):
        path = path.encode('utf-8')

    if os.path.isfile(path):
        if not os.path.basename(path).startswith(b'.'):
            yield path
    else:
        for dirpath, dirnames, filenames in os.walk(path, followlinks=True):
            for dirname in dirnames:
                if dirname.startswith(b'.'):
                    # Skip hidden dirs by modifying dirnames inplace
                    dirnames.remove(dirname)

            for filename in filenames:
                if filename.startswith(b'.'):
                    # Skip hidden files
                    continue

                yield os.path.join(dirpath, filename)


def check_file_path_is_inside_base_dir(file_path, base_path):
    assert not file_path.endswith(os.sep), (
        'File path %s cannot end with a path separator' % file_path)

    # Expand symlinks
    real_base_path = os.path.realpath(base_path)
    real_file_path = os.path.realpath(file_path)

    # Use dir of file for prefix comparision, so we don't accept
    # /tmp/foo.m3u as being inside /tmp/foo, simply because they have a
    # common prefix, /tmp/foo, which matches the base path, /tmp/foo.
    real_dir_path = os.path.dirname(real_file_path)

    # Check if dir of file is the base path or a subdir
    common_prefix = os.path.commonprefix([real_base_path, real_dir_path])
    assert common_prefix == real_base_path, (
        'File path %s must be in %s' % (real_file_path, real_base_path))


# FIXME replace with mock usage in tests.
class Mtime(object):
    def __init__(self):
        self.fake = None

    def __call__(self, path):
        if self.fake is not None:
            return self.fake
        return int(os.stat(path).st_mtime)

    def set_fake_time(self, time):
        self.fake = time

    def undo_fake(self):
        self.fake = None

mtime = Mtime()
