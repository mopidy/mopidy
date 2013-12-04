from __future__ import unicode_literals

import logging

from mopidy.backends import base

from . import translator

logger = logging.getLogger('mopidy.backends.local')


class LocalPlaybackProvider(base.BasePlaybackProvider):
    def change_track(self, track):
        track = track.copy(uri=translator.local_track_uri_to_file_uri(
            track.uri, self.backend.config['local']['media_dir']))
        return super(LocalPlaybackProvider, self).change_track(track)
