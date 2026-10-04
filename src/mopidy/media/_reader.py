from __future__ import annotations

from typing import TYPE_CHECKING, Self

from mopidy.media._gst.reader import GstMediaInfoReader

if TYPE_CHECKING:
    from types import TracebackType

    from mopidy.config import Config
    from mopidy.media._api import MediaInfoReader
    from mopidy.media._models import MediaInfo
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
    ) -> None:
        self._media_info_reader = media_info_reader
        self._timeout = timeout

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

    def close(self) -> None:
        """Release the resources of the reader."""

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
