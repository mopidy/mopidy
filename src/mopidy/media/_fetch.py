from __future__ import annotations

import dataclasses
import re
import time
import urllib.parse
from typing import TYPE_CHECKING

import httpx

from mopidy._lib.paths import uri_to_path
from mopidy.media._api import MediaReadError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from mopidy.types import DurationMs

_CHUNK_SIZE = 4096

# Control characters that do not occur in text, but often occur in media.
_BINARY_RE = re.compile(rb"[\x00-\x08\x0e-\x1f]")


@dataclasses.dataclass(frozen=True)
class Document:
    """The content of a URI that can be a playlist document."""

    data: bytes
    uri: str
    media_type: str | None = None


def fetch_document(
    *,
    http_client: httpx.Client,
    uri: str,
    timeout: DurationMs,
) -> Document | None:
    """Fetch the content of a `file`, `http` or `https` URI.

    The fetch stops at the first chunk that is not text, such as the body of
    an audio stream.

    Args:
        http_client: The HTTP client to fetch `http` and `https` URIs with.
        uri: The URI to fetch.
        timeout: The timeout for the fetch.

    Returns:
        The document, or `None` if the content is not text.

    Raises:
        MediaReadError: If the scheme is not supported, if the fetch fails,
            or on a timeout.
    """
    match urllib.parse.urlsplit(uri).scheme:
        case "file":
            return _fetch_file(
                uri=uri,
                timeout=timeout,
            )
        case "http" | "https":
            return _fetch_http(
                http_client=http_client,
                uri=uri,
                timeout=timeout,
            )
        case scheme:
            msg = f"Cannot fetch a playlist document with the scheme {scheme!r}"
            raise MediaReadError(msg)


def _fetch_file(
    *,
    uri: str,
    timeout: DurationMs,
) -> Document | None:
    try:
        with uri_to_path(uri).open("rb") as f:
            data = _read(
                chunks=iter(lambda: f.read(_CHUNK_SIZE), b""),
                timeout=timeout,
            )
    except OSError as exc:
        msg = f"Cannot read {uri}: {exc}"
        raise MediaReadError(msg) from exc
    if data is None:
        return None
    return Document(data=data, uri=uri)


def _fetch_http(
    *,
    http_client: httpx.Client,
    uri: str,
    timeout: DurationMs,
) -> Document | None:
    try:
        with http_client.stream("GET", uri, timeout=timeout / 1000) as response:
            if not response.is_success:
                msg = f"Cannot fetch {uri}: HTTP {response.status_code}"
                raise MediaReadError(msg)
            data = _read(
                chunks=response.iter_bytes(_CHUNK_SIZE),
                timeout=timeout,
            )
    except httpx.HTTPError as exc:
        msg = f"Cannot fetch {uri}: {exc}"
        raise MediaReadError(msg) from exc
    if data is None:
        return None
    return Document(
        data=data,
        uri=str(response.url),
        media_type=response.headers.get("content-type"),
    )


def _read(
    *,
    chunks: Iterable[bytes],
    timeout: DurationMs,
) -> bytes | None:
    deadline = time.monotonic() + timeout / 1000
    data = bytearray()
    for chunk in chunks:
        if _BINARY_RE.search(chunk):
            return None
        data += chunk
        if time.monotonic() > deadline:
            msg = "Timeout while fetching the playlist document"
            raise MediaReadError(msg)
    return bytes(data)
