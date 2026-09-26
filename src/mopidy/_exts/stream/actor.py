import fnmatch
import logging
import re
import time
import urllib.parse
from typing import override

import httpx
import pykka

from mopidy import audio as audio_lib
from mopidy import backend, exceptions
from mopidy.audio import (
    AudioProxy,
    MediaKind,
    Scanner,
    ScanResult,
    create_scanner,
)
from mopidy.config import Config
from mopidy.models import Track
from mopidy.types import DurationMs, Uri, UriScheme

from . import Extension, http
from .parsers import parse_playlist

logger = logging.getLogger(__name__)


class StreamBackend(pykka.ThreadingActor, backend.Backend):
    def __init__(self, *, config: Config, audio: AudioProxy) -> None:
        super().__init__(config=config, audio=audio)

        self._scanner = create_scanner(config, timeout=config["stream"]["timeout"])

        self._http_client = http.get_httpx_client(
            proxy_config=config["proxy"],
            user_agent=(f"{Extension.dist_name}/{Extension.version}"),
        )

        blacklist = config["stream"]["metadata_blacklist"]
        self._blacklist_re = re.compile(
            rf"^({'|'.join(fnmatch.translate(u) for u in blacklist)})$",
        )

        self._timeout = config["stream"]["timeout"]

        self.library = StreamLibraryProvider(backend=self)
        self.playback = StreamPlaybackProvider(audio=audio, backend=self)
        self.playlists = None

        uri_schemes = audio_lib.supported_uri_schemes(config["stream"]["protocols"])
        if UriScheme("file") in StreamBackend.uri_schemes and config["file"]["enabled"]:
            logger.warning(
                'The stream/protocols config value includes the "file" '
                'protocol. "file" playback is now handled by Mopidy-File. '
                "Please remove it from the stream/protocols config.",
            )
            uri_schemes -= {UriScheme("file")}
        StreamBackend.uri_schemes = sorted(uri_schemes)

    @override
    def on_stop(self) -> None:
        self._http_client.close()


class StreamLibraryProvider(backend.LibraryProvider):
    backend: StreamBackend

    @override
    def lookup(self, uri: Uri) -> list[Track]:
        if urllib.parse.urlsplit(uri).scheme not in self.backend.uri_schemes:
            return []

        if self.backend._blacklist_re.match(uri):
            logger.debug("URI matched metadata lookup blacklist: %s", uri)
            return [Track(uri=uri)]

        _, scan_result = _unwrap_stream(
            uri,
            timeout=self.backend._timeout,
            scanner=self.backend._scanner,
            http_client=self.backend._http_client,
        )

        if scan_result:
            # The scan followed the playlist to another URI, but the track is
            # looked up under the URI the caller asked for.
            track = scan_result.track.replace(uri=uri)
        else:
            logger.warning("Problem looking up %s", uri)
            track = Track(uri=uri)

        return [track]


class StreamPlaybackProvider(backend.PlaybackProvider):
    backend: StreamBackend

    @override
    def translate_uri(self, uri: Uri) -> Uri | None:
        if urllib.parse.urlsplit(uri).scheme not in self.backend.uri_schemes:
            return None

        if self.backend._blacklist_re.match(uri):
            logger.debug("URI matched metadata lookup blacklist: %s", uri)
            return uri

        unwrapped_uri, _ = _unwrap_stream(
            uri,
            timeout=self.backend._timeout,
            scanner=self.backend._scanner,
            http_client=self.backend._http_client,
        )
        return unwrapped_uri


def _unwrap_stream(  # noqa: PLR0911  # TODO: cleanup the return value of this.
    uri: Uri,
    timeout: float,
    scanner: Scanner,
    http_client: httpx.Client,
) -> tuple[Uri | None, ScanResult | None]:
    """Get a stream URI from a playlist URI, `uri`.

    Unwraps nested playlists until something that's not a playlist is found or
    the `timeout` is reached.
    """
    original_uri = uri
    seen_uris = set()
    deadline = time.time() + timeout

    while time.time() < deadline:
        if uri in seen_uris:
            logger.info(
                "Unwrapping stream from URI (%s) failed: playlist referenced itself",
                uri,
            )
            return None, None

        seen_uris.add(uri)

        logger.debug("Unwrapping stream from URI: %s", uri)

        try:
            scan_timeout = deadline - time.time()
            if scan_timeout < 0:
                logger.info(
                    "Unwrapping stream from URI (%s) failed: timed out in %sms",
                    uri,
                    timeout,
                )
                return None, None
            scan_result = scanner.scan(uri, timeout=DurationMs(int(scan_timeout)))
        except exceptions.ScannerError as exc:
            logger.debug("Failed scanning URI (%s): %s", uri, exc)
            scan_result = None

        if scan_result is not None and scan_result.kind is MediaKind.AUDIO:
            logger.debug(
                "Unwrapped potential %s stream: %s",
                scan_result.media_type,
                uri,
            )
            return uri, scan_result

        download_timeout = deadline - time.time()
        if download_timeout < 0:
            logger.info(
                "Unwrapping stream from URI (%s) failed: timed out in %sms",
                uri,
                timeout,
            )
            return None, None
        content = http.download(http_client, uri, timeout=download_timeout / 1000)

        if content is None:
            logger.info(
                "Unwrapping stream from URI (%s) failed: error downloading URI %s",
                original_uri,
                uri,
            )
            return None, None

        uris = parse_playlist(content)
        if not uris:
            logger.debug(
                "Failed parsing URI (%s) as playlist; found potential stream.",
                uri,
            )
            return uri, None

        # TODO: Test streams and return first that seems to be playable
        new_uri = uris[0]
        logger.debug("Parsed playlist (%s) and found new URI: %s", uri, new_uri)
        uri = Uri(urllib.parse.urljoin(uri, new_uri))

    return None, None
