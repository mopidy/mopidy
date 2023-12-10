import logging
from typing import ClassVar

import pykka

from mopidy import backend
from mopidy.file import library

# Event logging setup
logger = logging.getLogger(__name__)


class FileBackend(pykka.ThreadingActor, backend.Backend):
    # URI schemes supported by this backend
    uri_schemes: ClassVar[list[str]] = ["file"]

    def __init__(self, config, audio):
        # Backend initialization
        super().__init__()

        # File library provider
        self.library = library.FileLibraryProvider(backend=self, config=config)

        # Audio playback provider
        self.playback = backend.PlaybackProvider(audio=audio, backend=self)

        # Playlist initialization is not yet implemented
        self.playlists = None
