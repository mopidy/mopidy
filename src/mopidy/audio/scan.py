"""The deprecated scanner API.

[Scanner][mopidy.audio.scan.Scanner] here is replaced by
[create_scanner][mopidy.audio.create_scanner] and the
[Scanner][mopidy.audio.Scanner] it returns.
"""

import logging
from pathlib import Path
from typing import Any, NamedTuple
from warnings import deprecated

from mopidy._lib import logs
from mopidy.audio._gst.scan import scan_uri
from mopidy.config import ProxyConfig
from mopidy.types import DurationMs, Uri

logger = logging.getLogger(__name__)


class _Result(NamedTuple):
    uri: str
    tags: dict[str, Any]
    duration: DurationMs | None
    seekable: bool
    mime: str | None
    playable: bool


@deprecated(
    "mopidy.audio.scan.Scanner is deprecated since Mopidy 4.1 and will be "
    "removed in Mopidy 5.0. Use mopidy.audio.create_scanner() instead, which "
    "returns a mopidy.audio.Scanner giving you a mopidy.audio.ScanResult."
)
class Scanner:
    """Helper to get tags and other relevant info from URIs.

    !!! warning "Deprecated since Mopidy 4.1"

        Use [create_scanner][mopidy.audio.create_scanner] instead. This class
        is removed in Mopidy 5.0.

    Args:
        timeout: Timeout for scanning a URI in milliseconds.
        proxy_config: Dictionary containing proxy config strings.
    """

    def __init__(
        self,
        timeout: int = 1000,
        proxy_config: ProxyConfig | None = None,
    ) -> None:
        self._timeout_ms = int(timeout)
        self._proxy_config = proxy_config or None

    def scan(
        self,
        uri: str,
        timeout: float | None = None,
    ) -> _Result:
        """Scan the given URI collecting relevant metadata.

        Args:
            uri: URI of the resource to scan.
            timeout: Timeout for scanning in milliseconds. Defaults to the
                `timeout` value used when creating the scanner.

        Returns:
            Named tuple: `uri`, `tags`, `duration`, `seekable`, `mime`, `playable`.
        """
        data = scan_uri(
            uri,
            timeout_ms=int(timeout or self._timeout_ms),
            proxy_config=self._proxy_config,
        )
        return _Result(
            uri=uri,
            tags=data.tags,
            duration=data.duration,
            seekable=data.seekable,
            mime=data.mime,
            playable=data.has_audio,
        )


if __name__ == "__main__":
    import sys

    from mopidy import exceptions
    from mopidy._lib import paths
    from mopidy._lib.gi import Gst
    from mopidy.audio._gst.scan import GstScanner

    logging.basicConfig(
        format="%(asctime)-15s %(levelname)s %(message)s",
        level=logs.TRACE_LOG_LEVEL,
    )

    scanner = GstScanner(timeout=DurationMs(5000))
    for arg in sys.argv[1:]:
        uri = arg if Gst.uri_is_valid(arg) else paths.path_to_uri(Path(arg).resolve())
        try:
            result = scanner.scan(Uri(uri))
        except exceptions.ScannerError as error:
            print(f"{uri}: {error}")  # noqa: T201
            continue
        for key in ("uri", "kind", "media_type", "playable", "seekable"):
            print(f"{key:<20}   {getattr(result, key)}")  # noqa: T201
        print(f"{'images':<20}   {len(result.images)}")  # noqa: T201
        print("track")  # noqa: T201
        for field, value in result.track.serialize().items():
            line = f"{field:<20}   {value}"
            if len(line) > 77:
                line = line[:77] + "..."
            print(line)  # noqa: T201
