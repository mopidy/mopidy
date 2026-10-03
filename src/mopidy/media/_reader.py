from __future__ import annotations

from typing import TYPE_CHECKING, Self

import httpx

from mopidy import httpclient
from mopidy.media._fetch import fetch_document
from mopidy.media._gst.reader import GstMediaInfoReader
from mopidy.media._playlists import parse_playlist_entries

if TYPE_CHECKING:
    from types import TracebackType

    from mopidy.config import Config
    from mopidy.media._api import MediaInfoReader
    from mopidy.media._models import MediaInfo, PlaylistEntry
    from mopidy.types import DurationMs, Uri


class MediaReader:
    """Reads media without playing it.

    Make a reader with [create()][mopidy.media.MediaReader.create]. The reader is
    safe to call from many threads.
    """

    def __init__(
        self,
        *,
        media_info_reader: MediaInfoReader,
        timeout: DurationMs,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._media_info_reader = media_info_reader
        self._timeout = timeout
        self._http_client = http_client or httpx.Client(follow_redirects=True)

    @classmethod
    def create(cls, *, config: Config, timeout: DurationMs) -> Self:
        """Make a reader.

        Keep the reader, and close it with [close()][mopidy.media.MediaReader.close]
        when you do not need it anymore.

        Args:
            config: The Mopidy config. The reader uses the proxy config.
            timeout: The timeout for each read, in milliseconds.
        """
        return cls(
            media_info_reader=GstMediaInfoReader(proxy_config=config["proxy"]),
            timeout=timeout,
            http_client=httpx.Client(
                proxy=httpclient.format_proxy(config["proxy"]),
                headers={"user-agent": httpclient.format_user_agent()},
                follow_redirects=True,
            ),
        )

    def read_media_info(
        self,
        uri: Uri,
        *,
        timeout: DurationMs | None = None,
    ) -> MediaInfo:
        """Read the media info of one URI.

        Only the given URI is read. If the URI is a playlist document, the
        media info is not playable.

        Args:
            uri: The URI to read.
            timeout: The timeout. The default is the timeout of the reader.

        Raises:
            MediaReadError: If the URI cannot be read, or on a timeout.
        """
        if timeout is None:
            timeout = self._timeout
        return self._media_info_reader.read_media_info(uri, timeout=timeout)

    def read_playlist_entries(
        self,
        uri: Uri,
        *,
        timeout: DurationMs | None = None,
    ) -> tuple[PlaylistEntry, ...]:
        """Read the playlist entries of a playlist document.

        The playlist document is fetched from a `file`, `http` or `https` URI,
        and parsed with
        [parse_playlist_entries()][mopidy.media.parse_playlist_entries]. The
        HTTP `Content-Type` is the media type hint. Nested playlist documents
        are not read, and the media info of the entries is not read. The fetch
        stops at the first chunk that is not text, such as the body of an audio
        stream, and then there are no playlist entries.

        Args:
            uri: The URI of the playlist document.
            timeout: The timeout. The default is the timeout of the reader.

        Returns:
            The playlist entries, in the order of the playlist document.

        Raises:
            MediaReadError: If the scheme is not `file`, `http` or `https`, if
                the fetch fails, or on a timeout.
        """
        if timeout is None:
            timeout = self._timeout
        document = fetch_document(
            http_client=self._http_client, uri=uri, timeout=timeout
        )
        if document is None:
            return ()
        return parse_playlist_entries(
            document.data,
            base_uri=document.uri,
            media_type=document.media_type,
            uri=uri,
        )

    def close(self) -> None:
        """Release the resources of the reader."""
        self._http_client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
