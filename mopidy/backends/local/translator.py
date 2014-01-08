from __future__ import unicode_literals

import logging
import os
import urlparse
import urllib

from mopidy.utils.encoding import locale_decode
from mopidy.utils.path import path_to_uri, uri_to_path

logger = logging.getLogger(__name__)


def local_track_uri_to_file_uri(uri, media_dir):
    return path_to_uri(local_track_uri_to_path(uri, media_dir))


def local_track_uri_to_path(uri, media_dir):
    if not uri.startswith('local:track:'):
        raise ValueError('Invalid URI.')
    file_path = uri_to_path(uri).split(b':', 1)[1]
    return os.path.join(media_dir, file_path)


def path_to_local_track_uri(relpath):
    """Convert path releative to media_dir to local track URI."""
    if isinstance(relpath, unicode):
        relpath = relpath.encode('utf-8')
    return b'local:track:%s' % urllib.quote(relpath)


def parse_m3u(file_path, media_dir):
    r"""
    Convert M3U file list of uris

    Example M3U data::

        # This is a comment
        Alternative\Band - Song.mp3
        Classical\Other Band - New Song.mp3
        Stuff.mp3
        D:\More Music\Foo.mp3
        http://www.example.com:8000/Listen.pls
        http://www.example.com/~user/Mine.mp3

    - Relative paths of songs should be with respect to location of M3U.
    - Paths are normaly platform specific.
    - Lines starting with # should be ignored.
    - m3u files are latin-1.
    - This function does not bother with Extended M3U directives.
    """
    # TODO: uris as bytes
    uris = []
    try:
        with open(file_path) as m3u:
            contents = m3u.readlines()
    except IOError as error:
        logger.warning('Couldn\'t open m3u: %s', locale_decode(error))
        return uris

    for line in contents:
        line = line.strip().decode('latin1')

        if line.startswith('#'):
            continue

        if urlparse.urlsplit(line).scheme:
            uris.append(line)
        elif os.path.normpath(line) == os.path.abspath(line):
            path = path_to_uri(line)
            uris.append(path)
        else:
            path = path_to_uri(os.path.join(media_dir, line))
            uris.append(path)

    return uris
