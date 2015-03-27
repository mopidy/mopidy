from __future__ import absolute_import, unicode_literals

import logging
import os
import urllib

from mopidy import compat
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
    """Convert path relative to media_dir to local track URI."""
    if isinstance(relpath, compat.text_type):
        relpath = relpath.encode('utf-8')
    return b'local:track:%s' % urllib.quote(relpath)


def path_to_local_directory_uri(relpath):
    """Convert path relative to :confval:`local/media_dir` directory URI."""
    if isinstance(relpath, compat.text_type):
        relpath = relpath.encode('utf-8')
    return b'local:directory:%s' % urllib.quote(relpath)
