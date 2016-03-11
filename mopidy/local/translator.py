from __future__ import absolute_import, unicode_literals

import logging
import os
import urllib

from mopidy import compat
from mopidy.internal import path


logger = logging.getLogger(__name__)


def local_uri_to_file_uri(uri, media_dir):
    """Convert local track or directory URI to file URI."""
    return path_to_file_uri(local_uri_to_path(uri, media_dir))


def local_uri_to_path(uri, media_dir):
    """Convert local track or directory URI to absolute path."""
    if (
            not uri.startswith('local:directory:') and
            not uri.startswith('local:track:')):
        raise ValueError('Invalid URI.')
    file_path = path.uri_to_path(uri).split(b':', 1)[1]
    return os.path.join(media_dir, file_path)


def local_track_uri_to_path(uri, media_dir):
    # Deprecated version to keep old versions of Mopidy-Local-Sqlite working.
    return local_uri_to_path(uri, media_dir)


def path_to_file_uri(abspath):
    """Convert absolute path to file URI."""
    # Re-export internal method for use by Mopidy-Local-* extensions.
    return path.path_to_uri(abspath)


def path_to_local_track_uri(relpath):
    """Convert path relative to :confval:`local/media_dir` to local track
    URI."""
    if isinstance(relpath, compat.text_type):
        relpath = relpath.encode('utf-8')
    return 'local:track:%s' % urllib.quote(relpath)


def path_to_local_directory_uri(relpath):
    """Convert path relative to :confval:`local/media_dir` to directory URI."""
    if isinstance(relpath, compat.text_type):
        relpath = relpath.encode('utf-8')
    return 'local:directory:%s' % urllib.quote(relpath)
