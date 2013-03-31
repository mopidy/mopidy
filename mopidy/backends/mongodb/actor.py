from __future__ import unicode_literals

import logging

import pykka

from mopidy.backends import base

from .library import MongoDBLibraryProvider
from .playlists import MongoDBPlaylistsProvider

logger = logging.getLogger('mopidy.backends.mongodb')


class MongoDBBackend(pykka.ThreadingActor, base.Backend):
    def __init__(self, audio):
        super(MongoDBBackend, self).__init__()

        self.library = MongoDBLibraryProvider(backend=self)
        self.playback = base.BasePlaybackProvider(audio=audio, backend=self)
        self.playlists = MongoDBPlaylistsProvider(backend=self)

        self.uri_schemes = ['mongodb', 'file']
