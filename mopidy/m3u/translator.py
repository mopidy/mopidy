from __future__ import absolute_import, print_function, unicode_literals

import os

from mopidy import models

from . import Extension

try:
    from urllib.parse import quote_from_bytes, unquote_to_bytes
except ImportError:
    import urllib

    def quote_from_bytes(bytes, safe=b'/'):
        # Python 3 returns Unicode string
        return urllib.quote(bytes, safe).decode('utf-8')

    def unquote_to_bytes(string):
        if isinstance(string, bytes):
            return urllib.unquote(string)
        else:
            return urllib.unquote(string.encode('utf-8'))

try:
    from urllib.parse import urlsplit, urlunsplit
except ImportError:
    from urlparse import urlsplit, urlunsplit


try:
    from os import fsencode, fsdecode
except ImportError:
    import sys

    # no 'surrogateescape' in Python 2; 'replace' for backward compatibility
    def fsencode(filename, encoding=sys.getfilesystemencoding()):
        return filename.encode(encoding, 'replace')

    def fsdecode(filename, encoding=sys.getfilesystemencoding()):
        return filename.decode(encoding, 'replace')


def path_to_uri(path, scheme=Extension.ext_name):
    """Convert file path to URI."""
    assert isinstance(path, bytes), 'Mopidy paths should be bytes'
    uripath = quote_from_bytes(os.path.normpath(path))
    return urlunsplit((scheme, None, uripath, None, None))


def uri_to_path(uri):
    """Convert URI to file path."""
    # TODO: decide on Unicode vs. bytes for URIs
    return unquote_to_bytes(urlsplit(uri).path)


def name_from_path(path):
    """Extract name from file path."""
    name, _ = os.path.splitext(os.path.basename(path))
    try:
        return fsdecode(name)
    except UnicodeError:
        return None


def path_from_name(name, ext=None, sep='|'):
    """Convert name with optional extension to file path."""
    if ext:
        return fsencode(name.replace(os.sep, sep) + ext)
    else:
        return fsencode(name.replace(os.sep, sep))


def path_to_ref(path):
    return models.Ref.playlist(
        uri=path_to_uri(path),
        name=name_from_path(path)
    )


def load_items(fp, basedir):
    refs = []
    name = None
    for line in filter(None, (line.strip() for line in fp)):
        if line.startswith('#'):
            if line.startswith('#EXTINF:'):
                name = line.partition(',')[2]
            continue
        elif not urlsplit(line).scheme:
            path = os.path.join(basedir, fsencode(line))
            if not name:
                name = name_from_path(path)
            uri = path_to_uri(path, scheme='file')
        else:
            uri = line  # do *not* extract name from (stream?) URI path
        refs.append(models.Ref.track(uri=uri, name=name))
        name = None
    return refs


def dump_items(items, fp):
    if any(item.name for item in items):
        print('#EXTM3U', file=fp)
    for item in items:
        if item.name:
            print('#EXTINF:-1,%s' % item.name, file=fp)
        # TODO: convert file URIs to (relative) paths?
        if isinstance(item.uri, bytes):
            print(item.uri.decode('utf-8'), file=fp)
        else:
            print(item.uri, file=fp)


def playlist(path, items=[], mtime=None):
    return models.Playlist(
        uri=path_to_uri(path),
        name=name_from_path(path),
        tracks=[models.Track(uri=item.uri, name=item.name) for item in items],
        last_modified=(int(mtime * 1000) if mtime else None)
    )
