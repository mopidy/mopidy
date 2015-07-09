from __future__ import absolute_import, unicode_literals

import logging

import pykka

from mopidy import backend
from mopidy.file import library


logger = logging.getLogger(__name__)


class FilesBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes = ['file']

    def __init__(self, config, audio):
        super(FilesBackend, self).__init__()
        self.library = library.FilesLibraryProvider(backend=self,
                                                    config=config)
        self.playback = backend.PlaybackProvider(audio=audio, backend=self)
        self.playlists = None
