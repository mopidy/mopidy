from typing import Any, NamedTuple


class ScanResult(NamedTuple):
    uri: str
    tags: dict[str, Any]
    duration: int | None
    seekable: bool
    mime: str | None
    playable: bool


class ScannerBase:
    """Helper to get tags and other relevant info from URIs.

    :param timeout: timeout for scanning a URI in ms
    :param proxy_config: dictionary containing proxy config strings.
    """

    def __init__(
        self,
        timeout: int = 1000,
        proxy_config: dict[str, Any] | None = None,
    ) -> None:
        self._timeout_ms = int(timeout)
        self._proxy_config = proxy_config or {}

    def scan(
        self,
        uri: str,
        timeout: float | None = None,  # noqa: ARG002
    ) -> ScanResult:
        """Scan the given uri collecting relevant metadata.

        :param uri: URI of the resource to scan.
        :type uri: string
        :param timeout: timeout for scanning a URI in ms. Defaults to the
            ``timeout`` value used when creating the scanner.
        :type timeout: int
        :return: A named tuple containing
            ``(uri, tags, duration, seekable, mime)``.
            ``tags`` is a dictionary of lists for all the tags we found.
            ``duration`` is the length of the URI in milliseconds, or
            :class:`None` if the URI has no duration. ``seekable`` is boolean.
            indicating if a seek would succeed.
        """
        return ScanResult(
            uri=uri,
            tags={},
            duration=None,
            seekable=False,
            mime=None,
            playable=True,
        )
