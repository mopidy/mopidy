from __future__ import absolute_import, unicode_literals

import logging

import pykka

from mopidy import backend
from mopidy.file import library


logger = logging.getLogger(__name__)


class FileBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes = ['file']

    def __init__(self, config, audio):
        super(FileBackend, self).__init__()
        self.library = library.FileLibraryProvider(backend=self, config=config)
        self.playback = backend.PlaybackProvider(audio=audio, backend=self)
        self.playlists = None
