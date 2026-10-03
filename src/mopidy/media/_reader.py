from __future__ import annotations

import dataclasses
import logging
import time
import urllib.parse
from typing import TYPE_CHECKING, Self

import httpx

from mopidy import httpclient
from mopidy.media._api import MediaReadError
from mopidy.media._fetch import FETCH_SCHEMES, Document, fetch_document
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


class Reader:
    """Reads media without playing it.

    Make a reader with [create()][mopidy.media.Reader.create]. The reader is
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

        Keep the reader, and close it with [close()][mopidy.media.Reader.close]
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

    def read_media_info(self, uri: Uri) -> MediaInfo:
        """Read the media info of one URI.

        Only the given URI is read. If the URI is a playlist document, the
        media info is not playable.

        Args:
            uri: The URI to read.

        Raises:
            MediaReadError: If the URI cannot be read, or on a timeout.
        """
        return self._media_info_reader.read_media_info(uri, timeout=self._timeout)

    def read_playlist_entries(self, uri: Uri) -> tuple[PlaylistEntry, ...]:
        """Read the playlist entries of a playlist document.

        The playlist document is fetched from a `file`, `http` or `https` URI,
        and parsed with
        [parse_playlist_entries()][mopidy.media.parse_playlist_entries]. The
        HTTP `Content-Type` is the media type hint. Nested playlist documents
        are not read, and the media info of the entries is not read.

        Args:
            uri: The URI of the playlist document.

        Returns:
            The playlist entries, in the order of the playlist document.

        Raises:
            MediaReadError: If the scheme is not `file`, `http` or `https`, if
                the fetch fails, or on a timeout.
        """
        document = fetch_document(
            self._http_client,
            uri,
            deadline=time.monotonic() + self._timeout / 1000,
        )
        return _parse_entries(document, uri)

    def find_playback_target(self, uri: Uri) -> PlaybackTarget | None:
        """Find the playback target for a URI.

        The URI can be a playlist document, nested to any depth. For each
        playlist document, the alternatives of each entry are tried in order,
        and then the next entry. A URI that was tried before is not tried
        again. The timeout of the reader is the deadline for all reads.

        An `http` or `https` URI is fetched first. If the HTTP headers tell
        that the content is audio or video, the body is not read, and the
        media info is read. Else, the content is parsed as a playlist
        document. A `file` URI is also parsed first. Content that is not a
        playlist document and URIs with other schemes are read with
        [read_media_info()][mopidy.media.Reader.read_media_info].

        The reasons why each URI failed are logged.

        Args:
            uri: The URI to find the playback target for.

        Returns:
            The first playable URI. If there is none, the first URI that was
            fetched, but that is not a playlist document and has no playable
            media info, as an unverified playback target. `None` if nothing is
            found.
        """
        search = _Search(deadline=time.monotonic() + self._timeout / 1000)
        target = self._find(uri, None, search) or search.unverified
        if (target is None or target.info is None) and search.remaining() <= 0:
            logger.debug(
                "Stopped to find the playback target for %s at the deadline", uri
            )
        return target

    def _find(
        self,
        uri: Uri,
        entry: PlaylistEntry | None,
        search: _Search,
    ) -> PlaybackTarget | None:
        if uri in search.seen:
            logger.debug("Skipping %s: it was tried before", uri)
            return None
        search.seen.add(uri)

        fetched = urllib.parse.urlsplit(uri).scheme in FETCH_SCHEMES
        entries = ()
        if fetched:
            try:
                entries = self._read_entries_if_playlist_document(uri, search)
            except MediaReadError as exc:
                logger.debug("Cannot read playlist document %s: %s", uri, exc)
                fetched = False
        if entries:
            return self._find_in_entries(entries, search)
        timeout = DurationMs(int(search.remaining() * 1000))
        if timeout <= 0:
            return None

        try:
            info = self._media_info_reader.read_media_info(uri, timeout=timeout)
        except MediaReadError as exc:
            logger.debug("Cannot read media info of %s: %s", uri, exc)
        else:
            if info.playable:
                return PlaybackTarget(uri=uri, info=info, entry=entry)
            logger.debug("Media info of %s is not playable", uri)
        if fetched and search.unverified is None:
            search.unverified = PlaybackTarget(uri=uri, info=None, entry=entry)
        return None

    def _find_in_entries(
        self,
        entries: tuple[PlaylistEntry, ...],
        search: _Search,
    ) -> PlaybackTarget | None:
        for entry in entries:
            for alternative in entry.alternatives:
                if search.remaining() <= 0:
                    return None
                if target := self._find(alternative, entry, search):
                    return target
        return None

    def _read_entries_if_playlist_document(
        self,
        uri: Uri,
        search: _Search,
    ) -> tuple[PlaylistEntry, ...]:
        document = fetch_document(
            self._http_client,
            uri,
            deadline=search.deadline,
            stop_at_media=True,
        )
        return _parse_entries(document, uri)

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
class _Search:
    deadline: float
    seen: set[Uri] = dataclasses.field(default_factory=set)
    unverified: PlaybackTarget | None = None

    def remaining(self) -> float:
        return max(self.deadline - time.monotonic(), 0)


def _parse_entries(document: Document | None, uri: Uri) -> tuple[PlaylistEntry, ...]:
    if document is None:
        return ()
    return parse_playlist_entries(
        document.data,
        base_uri=document.uri,
        media_type=document.media_type,
        uri=uri,
    )
