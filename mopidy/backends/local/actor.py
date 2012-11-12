from __future__ import unicode_literals

import logging

import pykka

from mopidy.backends import base

from .library import LocalLibraryProvider
from .stored_playlists import LocalStoredPlaylistsProvider

logger = logging.getLogger('mopidy.backends.local')


class LocalBackend(pykka.ThreadingActor, base.Backend):
    def __init__(self, audio):
        super(LocalBackend, self).__init__()

        self.library = LocalLibraryProvider(backend=self)
        self.playback = base.BasePlaybackProvider(audio=audio, backend=self)
        self.stored_playlists = LocalStoredPlaylistsProvider(backend=self)

        self.uri_schemes = ['file']
