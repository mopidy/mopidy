from __future__ import annotations

import os
import urllib.parse
from collections.abc import Iterable
from pathlib import Path
from typing import IO

from mopidy.internal import path
from mopidy.models import Playlist, Ref, Track
from mopidy.types import Uri

from . import Extension


def path_to_uri(
    path: Path,
    scheme: str = Extension.ext_name,
) -> Uri:
    """Convert file path to URI."""
    bytes_path = os.path.normpath(bytes(path))
    uripath = urllib.parse.quote_from_bytes(bytes_path)
    return Uri(urllib.parse.urlunsplit((scheme, None, uripath, None, None)))


def uri_to_path(uri: Uri) -> Path:
    """Convert URI to file path."""
    return path.uri_to_path(uri)


def name_from_path(path: Path) -> str | None:
    """Extract name from file path."""
    name = bytes(Path(path.stem))
    try:
        return name.decode(errors="replace")
    except UnicodeError:
        return None


def path_from_name(
    name: str,
    ext: str | None = None,
    sep: str = "|",
) -> Path:
    """Convert name with optional extension to file path."""
    name = name.replace(os.sep, sep) + ext if ext else name.replace(os.sep, sep)
    return Path(name)


def path_to_ref(path: Path) -> Ref:
    return Ref.playlist(uri=path_to_uri(path), name=name_from_path(path))


def load_items(
    fp: IO[str],
    basedir: Path,
) -> list[Ref]:
    refs = []
    name = None
    for line in filter(None, (line.strip() for line in fp)):
        if line.startswith("#"):
            if line.startswith("#EXTINF:"):
                name = line.partition(",")[2]
            continue
        if not urllib.parse.urlsplit(line).scheme:
            path = basedir / line
            if not name:
                name = name_from_path(path)
            uri = path_to_uri(path, scheme="file")
        else:
            # TODO: ensure this is urlencoded
            uri = Uri(line)  # do *not* extract name from (stream?) URI path
        refs.append(Ref.track(uri=uri, name=name))
        name = None
    return refs


def dump_items(
    items: Iterable[Ref | Track],
    fp: IO[str],
) -> None:
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


def playlist(
    path: Path,
    items: Iterable[Ref | Track] | None = None,
    mtime: float | None = None,
) -> Playlist:
    if items is None:
        items = []
    return Playlist(
        uri=path_to_uri(path),
        name=name_from_path(path),
        tracks=tuple(Track(uri=item.uri, name=item.name) for item in items),
        last_modified=(int(mtime * 1000) if mtime else None),
    )
