from __future__ import unicode_literals

import logging

from mopidy.backends import base

from . import translator

logger = logging.getLogger('mopidy.backends.local')


class LocalPlaybackProvider(base.BasePlaybackProvider):
    def change_track(self, track):
        media_dir = self.backend.config['local']['media_dir']
        uri = translator.local_to_file_uri(track.uri, media_dir)
        track = track.copy(uri=uri)
        return super(LocalPlaybackProvider, self).change_track(track)
