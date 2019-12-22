import os
import pathlib
import urllib

from mopidy import models
from mopidy.internal import path

from . import Extension


def path_to_uri(path, scheme=Extension.ext_name):
    """Convert file path to URI."""
    bytes_path = os.path.normpath(bytes(path))
    uripath = urllib.parse.quote_from_bytes(bytes_path)
    return urllib.parse.urlunsplit((scheme, None, uripath, None, None))


def uri_to_path(uri):
    """Convert URI to file path."""
    return path.uri_to_path(uri)


def name_from_path(path):
    """Extract name from file path."""
    name = bytes(pathlib.Path(path.stem))
    try:
        return name.decode(errors="replace")
    except UnicodeError:
        return None


def path_from_name(name, ext=None, sep="|"):
    """Convert name with optional extension to file path."""
    if ext:
        name = name.replace(os.sep, sep) + ext
    else:
        name = name.replace(os.sep, sep)
    return pathlib.Path(name)


def path_to_ref(path):
    return models.Ref.playlist(uri=path_to_uri(path), name=name_from_path(path))


def load_items(fp, basedir):
    refs = []
    name = None
    for line in filter(None, (line.strip() for line in fp)):
        if line.startswith("#"):
            if line.startswith("#EXTINF:"):
                name = line.partition(",")[2]
            continue
        elif not urllib.parse.urlsplit(line).scheme:
            path = basedir / line
            if not name:
                name = name_from_path(path)
            uri = path_to_uri(path, scheme="file")
        else:
            # TODO: ensure this is urlencoded
            uri = line  # do *not* extract name from (stream?) URI path
        refs.append(models.Ref.track(uri=uri, name=name))
        name = None
    return refs


def dump_items(items, fp):
    if any(item.name for item in items):
        print("#EXTM3U", file=fp)
    for item in items:
        if item.name:
            print(f"#EXTINF:-1,{item.name}", file=fp)
        # TODO: convert file URIs to (relative) paths?
        if isinstance(item.uri, bytes):
            print(item.uri.decode(), file=fp)
        else:
            print(item.uri, file=fp)


def playlist(path, items=None, mtime=None):
    if items is None:
        items = []
    return models.Playlist(
        uri=path_to_uri(path),
        name=name_from_path(path),
        tracks=[models.Track(uri=item.uri, name=item.name) for item in items],
        last_modified=(int(mtime * 1000) if mtime else None),
    )
