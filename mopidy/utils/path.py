from __future__ import unicode_literals

import logging
import os
import string
import urllib
import urlparse

import glib


logger = logging.getLogger('mopidy.utils.path')


XDG_DIRS = {
    'XDG_CACHE_DIR': glib.get_user_cache_dir(),
    'XDG_CONFIG_DIR': glib.get_user_config_dir(),
    'XDG_DATA_DIR': glib.get_user_data_dir(),
    'XDG_MUSIC_DIR': glib.get_user_special_dir(glib.USER_DIRECTORY_MUSIC),
}

# XDG_MUSIC_DIR can be none, so filter out any bad data.
XDG_DIRS = dict((k, v) for k, v in XDG_DIRS.items() if v is not None)


def get_or_create_dir(dir_path):
    if not isinstance(dir_path, bytes):
        raise ValueError('Path is not a bytestring.')
    dir_path = expand_path(dir_path)
    if os.path.isfile(dir_path):
        raise OSError(
            'A file with the same name as the desired dir, '
            '"%s", already exists.' % dir_path)
    elif not os.path.isdir(dir_path):
        logger.info('Creating dir %s', dir_path)
        os.makedirs(dir_path, 0755)
    return dir_path


def get_or_create_file(file_path, mkdir=True, content=None):
    if not isinstance(file_path, bytes):
        raise ValueError('Path is not a bytestring.')
    file_path = expand_path(file_path)
    if mkdir:
        get_or_create_dir(os.path.dirname(file_path))
    if not os.path.isfile(file_path):
        logger.info('Creating file %s', file_path)
        with open(file_path, 'w') as fh:
            if content:
                fh.write(content)
    return file_path


def path_to_uri(path):
    """
    Convert OS specific path to file:// URI.

    Accepts either unicode strings or bytestrings. The encoding of any
    bytestring will be maintained so that :func:`uri_to_path` can return the
    same bytestring.

    Returns a file:// URI as an unicode string.
    """
    if isinstance(path, unicode):
        path = path.encode('utf-8')
    path = urllib.quote(path)
    return urlparse.urlunsplit((b'file', b'', path, b'', b''))


def uri_to_path(uri):
    """
    Convert an URI to a OS specific path.

    Returns a bytestring, since the file path can contain chars with other
    encoding than UTF-8.

    If we had returned these paths as unicode strings, you wouldn't be able to
    look up the matching dir or file on your file system because the exact path
    would be lost by ignoring its encoding.
    """
    if isinstance(uri, unicode):
        uri = uri.encode('utf-8')
    return urllib.unquote(urlparse.urlsplit(uri).path)


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
    # TODO: document as we want people to use this.
    if not isinstance(path, bytes):
        raise ValueError('Path is not a bytestring.')
    try:
        path = string.Template(path).substitute(XDG_DIRS)
    except KeyError:
        return None
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


def find_uris(path):
    for p in find_files(path):
        yield path_to_uri(p)


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
