from __future__ import annotations

import dataclasses
import time
import urllib.parse
from typing import TYPE_CHECKING

import httpx

from mopidy._lib.paths import uri_to_path
from mopidy.media._api import MediaReadError

if TYPE_CHECKING:
    from collections.abc import Iterable

_CHUNK_SIZE = 4096


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
) -> Document:
    """Fetch the content of a `file`, `http` or `https` URI.

    Raises:
        MediaReadError: If the scheme is not supported, if the fetch fails,
            or at the deadline.
    """
    scheme = urllib.parse.urlsplit(uri).scheme
    if scheme == "file":
        return _fetch_file(uri, deadline=deadline)
    if scheme in ("http", "https"):
        return _fetch_http(http_client, uri, deadline=deadline)
    msg = f"Cannot fetch a playlist document with the scheme {scheme!r}"
    raise MediaReadError(msg)


def _fetch_file(uri: str, *, deadline: float) -> Document:
    try:
        with uri_to_path(uri).open("rb") as f:
            data = _read(iter(lambda: f.read(_CHUNK_SIZE), b""), deadline)
    except OSError as exc:
        msg = f"Cannot read {uri}: {exc}"
        raise MediaReadError(msg) from exc
    return Document(data=data, uri=uri)


def _fetch_http(http_client: httpx.Client, uri: str, *, deadline: float) -> Document:
    try:
        with http_client.stream("GET", uri, timeout=_remaining(deadline)) as response:
            if not response.is_success:
                msg = f"Cannot fetch {uri}: HTTP {response.status_code}"
                raise MediaReadError(msg)
            data = _read(response.iter_bytes(_CHUNK_SIZE), deadline)
    except httpx.HTTPError as exc:
        msg = f"Cannot fetch {uri}: {exc}"
        raise MediaReadError(msg) from exc
    return Document(
        data=data,
        uri=str(response.url),
        media_type=response.headers.get("content-type"),
    )


def _read(chunks: Iterable[bytes], deadline: float) -> bytes:
    data = bytearray()
    for chunk in chunks:
        data += chunk
        if time.monotonic() > deadline:
            msg = "Timeout while fetching the playlist document"
            raise MediaReadError(msg)
    return bytes(data)


def _remaining(deadline: float) -> float:
    return max(deadline - time.monotonic(), 0)
