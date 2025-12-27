import logging
from typing import ClassVar, override

import pykka

from mopidy import backend
from mopidy.audio import AudioProxy
from mopidy.config import Config
from mopidy.types import UriScheme

from . import library

logger = logging.getLogger(__name__)


class FileBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes: ClassVar[list[UriScheme]] = [UriScheme("file")]

    @override
    def __init__(self, config: Config, audio: AudioProxy) -> None:
        super().__init__()
        self.library = library.FileLibraryProvider(backend=self, config=config)
        self.playback = backend.PlaybackProvider(audio=audio, backend=self)
        self.playlists = None
