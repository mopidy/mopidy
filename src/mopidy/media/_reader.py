from __future__ import annotations

import dataclasses
import logging
import time
from typing import TYPE_CHECKING, Self

import httpx

from mopidy import httpclient
from mopidy.media._api import MediaReadError
from mopidy.media._fetch import fetch_document
from mopidy.media._gst.reader import GstMediaInfoReader
from mopidy.media._models import PlaybackTarget
from mopidy.media._playlists import parse_playlist_entries
from mopidy.types import DurationMs

if TYPE_CHECKING:
    from types import TracebackType

    from mopidy.config import Config
    from mopidy.media._api import MediaInfoReader
    from mopidy.media._models import MediaInfo, PlaylistEntry
    from mopidy.types import Uri

logger = logging.getLogger(__name__)


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

    def find_playback_target(
        self,
        uri: Uri,
        *,
        timeout: DurationMs | None = None,
    ) -> PlaybackTarget | None:
        """Find the playback target for a URI.

        The URI can be a playlist document, nested to any depth. For each
        playlist document, the alternatives of each entry are tried in order,
        and then the next entry. A URI that was tried before is not tried
        again. The timeout is the deadline for all reads.

        Each URI is first read as a playlist document with
        [read_playlist_entries()][mopidy.media.MediaReader.read_playlist_entries],
        so the body of an audio stream is not read. If the URI gives no
        playlist entries, it is read with
        [read_media_info()][mopidy.media.MediaReader.read_media_info].

        The reasons why each URI failed are logged.

        Args:
            uri: The URI to find the playback target for.
            timeout: The deadline for all reads. The default is the timeout of
                the reader.

        Returns:
            The first playable URI. If there is none, the first URI that was
            fetched, but that is not a playlist document and has no playable
            media info, as an unverified playback target. `None` if nothing is
            found.
        """
        if timeout is None:
            timeout = self._timeout
        state = _PlaybackTargetSearchState(deadline=time.monotonic() + timeout / 1000)
        target = self._try_uri(uri=uri, entry=None, state=state) or state.unverified
        if (target is None or target.info is None) and state.remaining() <= 0:
            logger.debug(
                "Stopped the search for the playback target for %s at the deadline", uri
            )
        return target

    def _try_uri(
        self,
        *,
        uri: Uri,
        entry: PlaylistEntry | None,
        state: _PlaybackTargetSearchState,
    ) -> PlaybackTarget | None:
        if state.remaining() <= 0:
            return None
        if uri in state.seen:
            logger.debug("Skipping %s: it was tried before", uri)
            return None
        state.seen.add(uri)

        fetch_failed = False
        try:
            entries = self.read_playlist_entries(uri, timeout=state.remaining())
        except MediaReadError as exc:
            logger.debug("Cannot read playlist document %s: %s", uri, exc)
            entries = ()
            fetch_failed = True
        if entries:
            targets = (
                self._try_uri(uri=alternative, entry=child, state=state)
                for child in entries
                for alternative in child.alternatives
            )
            return next(filter(None, targets), None)

        if state.remaining() <= 0:
            return None

        try:
            info = self.read_media_info(uri, timeout=state.remaining())
        except MediaReadError as exc:
            logger.debug("Cannot read media info of %s: %s", uri, exc)
        else:
            if info.playable:
                return PlaybackTarget(uri=uri, info=info, entry=entry)
            logger.debug("Media info of %s is not playable", uri)
        if not fetch_failed and state.unverified is None:
            state.unverified = PlaybackTarget(uri=uri, info=None, entry=entry)
        return None

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


@dataclasses.dataclass
class _PlaybackTargetSearchState:
    deadline: float
    seen: set[Uri] = dataclasses.field(default_factory=set)
    unverified: PlaybackTarget | None = None

    def remaining(self) -> DurationMs:
        return DurationMs(max(int((self.deadline - time.monotonic()) * 1000), 0))
