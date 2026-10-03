import fnmatch
import logging
import re
import urllib.parse
from typing import override

import pykka

from mopidy import audio as audio_lib
from mopidy import backend
from mopidy.audio import AudioProxy
from mopidy.config import Config
from mopidy.media import Reader
from mopidy.models import Track
from mopidy.types import DurationMs, Uri, UriScheme

logger = logging.getLogger(__name__)


class StreamBackend(pykka.ThreadingActor, backend.Backend):
    def __init__(self, *, config: Config, audio: AudioProxy) -> None:
        super().__init__(config=config, audio=audio)

        self._media_reader = Reader.create(
            config=config,
            timeout=DurationMs(config["stream"]["timeout"]),
        )

        blacklist = config["stream"]["metadata_blacklist"]
        self._blacklist_re = re.compile(
            rf"^({'|'.join(fnmatch.translate(u) for u in blacklist)})$",
        )

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
        self._media_reader.close()


class StreamLibraryProvider(backend.LibraryProvider):
    backend: StreamBackend

    @override
    def lookup(self, uri: Uri) -> list[Track]:
        if urllib.parse.urlsplit(uri).scheme not in self.backend.uri_schemes:
            return []

        if self.backend._blacklist_re.match(uri):
            logger.debug("URI matched metadata lookup blacklist: %s", uri)
            return [Track(uri=uri)]

        target = self.backend._media_reader.find_playback_target(uri)

        if target and target.info:
            track = target.info.track.replace(uri=uri)
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

        target = self.backend._media_reader.find_playback_target(uri)
        return target.uri if target else None
