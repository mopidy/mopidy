import logging
from pathlib import Path
from typing import Any, NamedTuple

from mopidy import exceptions
from mopidy._lib import logs
from mopidy._lib.gi import Gst
from mopidy.config import ProxyConfig
from mopidy.media._gst.pipeline import read_media_data
from mopidy.types import DurationMs


class _Result(NamedTuple):
    uri: str
    tags: dict[str, Any]
    duration: DurationMs | None
    seekable: bool
    mime: str | None
    playable: bool


# TODO: replace with a scan(uri, timeout=1000, proxy_config=None)?
class Scanner:
    """Helper to get tags and other relevant info from URIs.

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
        data = read_media_data(
            uri,
            timeout_ms=int(timeout or self._timeout_ms),
            proxy_config=self._proxy_config,
        )
        return _Result(
            uri,
            data.tags,
            data.duration,
            data.seekable,
            data.mime,
            data.playable,
        )


if __name__ == "__main__":
    import sys

    from mopidy._lib import paths

    logging.basicConfig(
        format="%(asctime)-15s %(levelname)s %(message)s",
        level=logs.TRACE_LOG_LEVEL,
    )

    scanner = Scanner(5000)
    for uri in sys.argv[1:]:
        if not Gst.uri_is_valid(uri):
            uri = paths.path_to_uri(Path(uri).resolve())
        try:
            result = scanner.scan(uri)
            for key in ("uri", "mime", "duration", "playable", "seekable"):
                value = getattr(result, key)
                print(f"{key:<20}   {value}")  # noqa: T201
            print("tags")  # noqa: T201
            for tag, value in result.tags.items():
                line = f"{tag:<20}   {value}"
                if len(line) > 77:
                    line = line[:77] + "..."
                print(line)  # noqa: T201
        except exceptions.ScannerError as error:
            print(f"{uri}: {error}")  # noqa: T201
