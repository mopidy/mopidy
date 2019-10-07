from __future__ import absolute_import, unicode_literals

import logging
import os
import re


from mopidy import compat
from mopidy.compat import pathlib, urllib
from mopidy.internal import xdg
# Reexport in old location for Mopidy-Local's use
from mopidy.internal.mtimes import find_mtimes  # noqa


logger = logging.getLogger(__name__)


XDG_DIRS = xdg.get_dirs()


def get_or_create_dir(dir_path):
    dir_path = expand_path(dir_path)
    if dir_path.is_file():
        raise OSError(
            'A file with the same name as the desired dir, '
            '"%s", already exists.' % dir_path)
    elif not dir_path.is_dir():
        logger.info('Creating dir %s', dir_path)
        dir_path.mkdir(mode=0o755, parents=True)
    return dir_path


def get_or_create_file(file_path, mkdir=True, content=None):
    file_path = expand_path(file_path)
    if isinstance(content, compat.text_type):
        content = content.encode('utf-8')
    if mkdir:
        get_or_create_dir(file_path.parent)
    if not file_path.is_file():
        logger.info('Creating file %s', file_path)
        file_path.touch(exist_ok=False)
        if content is not None:
            file_path.write_bytes(content)
    return file_path


def get_unix_socket_path(socket_path):
    match = re.search('^unix:(.*)', socket_path)
    if not match:
        return None
    return match.group(1)


def path_to_uri(path):
    """
    Convert OS specific path to file:// URI.

    Accepts either unicode strings or bytestrings. The encoding of any
    bytestring will be maintained so that :func:`uri_to_path` can return the
    same bytestring.

    Returns a file:// URI as an unicode string.
    """
    return pathlib.Path(path).as_uri()


def uri_to_path(uri):
    """
    Convert an URI to a OS specific path.
    """
    if compat.PY2:
        if isinstance(uri, compat.text_type):
            uri = uri.encode('utf-8')
        bytes_path = urllib.parse.unquote(urllib.parse.urlsplit(uri).path)
        return pathlib.Path(bytes_path)
    else:
        bytes_path = urllib.parse.unquote_to_bytes(
            urllib.parse.urlsplit(uri).path)
        unicode_path = bytes_path.decode('utf-8', 'surrogateescape')
        return pathlib.Path(unicode_path)


def expand_path(path):
    path = str(pathlib.Path(path))
    for xdg_var, xdg_dir in XDG_DIRS.items():
        # py-compat: First str() is to get native strings on both Py2/Py3
        path = path.replace(str('$' + xdg_var), str(xdg_dir))
    if '$' in path:
        return None
    return pathlib.Path(path).expanduser().resolve()


def is_path_inside_base_dir(path, base_path):
    if not isinstance(path, bytes):
        raise TypeError('path is not a bytestring')
    if not isinstance(base_path, bytes):
        raise TypeError('base_path is not a bytestring')

    if compat.PY2:
        path_separator = os.sep
    else:
        path_separator = os.sep.encode()

    if path.endswith(path_separator):
        raise ValueError(
            'path %r cannot end with a path separator' % path)

    # Expand symlinks
    real_base_path = os.path.realpath(base_path)
    real_path = os.path.realpath(path)

    if os.path.isfile(path):
        # Use dir of file for prefix comparision, so we don't accept
        # /tmp/foo.m3u as being inside /tmp/foo, simply because they have a
        # common prefix, /tmp/foo, which matches the base path, /tmp/foo.
        real_path = os.path.dirname(real_path)

    # Check if dir of file is the base path or a subdir
    common_prefix = os.path.commonprefix([real_base_path, real_path])
    return common_prefix == real_base_path
