from typing import Any, NamedTuple

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
