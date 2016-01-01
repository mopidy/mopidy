from __future__ import absolute_import, unicode_literals

import pykka

from mopidy import backend

from . import playlists


class M3UBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes = ['m3u']

    def __init__(self, config, audio):
        super(M3UBackend, self).__init__()
        self.playlists = playlists.M3UPlaylistsProvider(self, config)
