"""The deprecated scanner API.

Use
[MediaReader.read_media_info()][mopidy.media.MediaReader.read_media_info] instead.
"""

from typing import Any, NamedTuple
from warnings import deprecated

from mopidy import exceptions
from mopidy.config import ProxyConfig
from mopidy.media import MediaReaderError
from mopidy.media._gst.reader import GstRead
from mopidy.types import DurationMs, Uri


class _Result(NamedTuple):
    uri: str
    tags: dict[str, Any]
    duration: DurationMs | None
    seekable: bool
    mime: str | None
    playable: bool


@deprecated(
    "mopidy.audio.scan.Scanner is deprecated since Mopidy 4.1, and will be "
    "removed in Mopidy 5.0. Use mopidy.media.MediaReader.read_media_info() "
    "instead."
)
class Scanner:
    """Helper to get tags and other relevant info from URIs.

    /// warning | Deprecated
    Deprecated since Mopidy 4.1, and will be removed in Mopidy 5.0. Use
    [MediaReader.read_media_info()][mopidy.media.MediaReader.read_media_info] instead.
    ///

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
        try:
            result = GstRead(
                Uri(uri),
                timeout=DurationMs(int(timeout or self._timeout_ms)),
                proxy_config=self._proxy_config,
            ).run()
        except MediaReaderError as exc:
            raise exceptions.ScannerError(str(exc)) from exc
        return _Result(
            uri,
            result.legacy_scanner_tags,
            result.info.track.length,
            result.info.seekable,
            result.legacy_scanner_mime,
            result.info.playable,
        )
