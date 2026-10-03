from __future__ import annotations

import dataclasses
import re
import time
import urllib.parse
from typing import TYPE_CHECKING

import httpx

from mopidy._lib.paths import uri_to_path
from mopidy.media._api import MediaReadError
from mopidy.media._playlists import is_playlist_media_type

if TYPE_CHECKING:
    from collections.abc import Iterable

FETCH_SCHEMES = frozenset({"file", "http", "https"})

_CHUNK_SIZE = 4096

# Control characters that do not occur in text, but often occur in media.
_BINARY_RE = re.compile(rb"[\x00-\x08\x0e-\x1f]")

_MEDIA_TYPES = frozenset({"application/dash+xml", "application/ogg"})


@dataclasses.dataclass(frozen=True)
class Document:
    """The content of a URI that can be a playlist document."""

    data: bytes
    uri: str
    media_type: str | None = None


def fetch_document(
    http_client: httpx.Client,
    uri: str,
    *,
    deadline: float,
    stop_at_media: bool = False,
) -> Document | None:
    """Fetch the content of a `file`, `http` or `https` URI.

    Returns `None` if the content is media, and not text. If `stop_at_media`
    is set, an audio or video media type in the HTTP headers also tells that
    the content is media, and then the body is not read.

    Raises:
        MediaReadError: If the scheme is not supported, if the fetch fails,
            or at the deadline.
    """
    scheme = urllib.parse.urlsplit(uri).scheme
    if scheme == "file":
        return _fetch_file(uri, deadline=deadline)
    if scheme in ("http", "https"):
        return _fetch_http(
            http_client,
            uri,
            deadline=deadline,
            stop_at_media=stop_at_media,
        )
    msg = f"Cannot fetch a playlist document with the scheme {scheme!r}"
    raise MediaReadError(msg)


def _fetch_file(uri: str, *, deadline: float) -> Document | None:
    try:
        with uri_to_path(uri).open("rb") as f:
            data = _read(iter(lambda: f.read(_CHUNK_SIZE), b""), deadline)
    except OSError as exc:
        msg = f"Cannot read {uri}: {exc}"
        raise MediaReadError(msg) from exc
    if data is None:
        return None
    return Document(data=data, uri=uri)


def _fetch_http(
    http_client: httpx.Client,
    uri: str,
    *,
    deadline: float,
    stop_at_media: bool,
) -> Document | None:
    try:
        with http_client.stream("GET", uri, timeout=_remaining(deadline)) as response:
            if not response.is_success:
                msg = f"Cannot fetch {uri}: HTTP {response.status_code}"
                raise MediaReadError(msg)
            media_type = response.headers.get("content-type")
            if stop_at_media and _is_media_type(media_type):
                return None
            data = _read(response.iter_bytes(_CHUNK_SIZE), deadline)
    except httpx.HTTPError as exc:
        msg = f"Cannot fetch {uri}: {exc}"
        raise MediaReadError(msg) from exc
    if data is None:
        return None
    return Document(data=data, uri=str(response.url), media_type=media_type)


def _read(chunks: Iterable[bytes], deadline: float) -> bytes | None:
    data = bytearray()
    for chunk in chunks:
        if _BINARY_RE.search(chunk):
            return None
        data += chunk
        if time.monotonic() > deadline:
            msg = "Timeout while fetching the playlist document"
            raise MediaReadError(msg)
    return bytes(data)


def _is_media_type(media_type: str | None) -> bool:
    if media_type is None:
        return False
    media_type = media_type.split(";", maxsplit=1)[0].strip().lower()
    if is_playlist_media_type(media_type):
        return False
    return media_type.startswith(("audio/", "video/")) or media_type in _MEDIA_TYPES


def _remaining(deadline: float) -> float:
    return max(deadline - time.monotonic(), 0)
