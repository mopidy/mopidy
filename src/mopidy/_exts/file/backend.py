import logging
from typing import ClassVar, override

import pykka

from mopidy import backend
from mopidy.audio import AudioProxy
from mopidy.config import Config
from mopidy.media import MediaReader
from mopidy.types import DurationMs, UriScheme

from . import library

logger = logging.getLogger(__name__)


class FileBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes: ClassVar[list[UriScheme]] = [UriScheme("file")]

    def __init__(self, *, config: Config, audio: AudioProxy) -> None:
        super().__init__(config=config, audio=audio)
        self._media_reader = MediaReader.create(
            config=config,
            timeout=DurationMs(config["file"]["metadata_timeout"]),
        )
        self.library = library.FileLibraryProvider(
            backend=self,
            config=config,
            media_reader=self._media_reader,
        )
        self.playback = backend.PlaybackProvider(audio=audio, backend=self)
        self.playlists = None

    @override
    def on_stop(self) -> None:
        self._media_reader.close()
