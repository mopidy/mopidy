from __future__ import unicode_literals

import logging

import pykka

from mopidy.backends import base

from .library import BeetsLibraryProvider

logger = logging.getLogger('mopidy.backends.beets')


class BeetsBackend(pykka.ThreadingActor, base.Backend):
    def __init__(self, audio):
        super(BeetsBackend, self).__init__()

        self.library = BeetsLibraryProvider(backend=self)
        self.playback = base.BasePlaybackProvider(audio=audio, backend=self)
        self.playlists = None

        self.uri_schemes = ['beets']
