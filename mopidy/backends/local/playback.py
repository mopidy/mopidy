from __future__ import unicode_literals

import logging
import os

from mopidy.backends import base
from mopidy.utils import path

logger = logging.getLogger('mopidy.backends.local')


class LocalPlaybackProvider(base.BasePlaybackProvider):
    def change_track(self, track):
        media_dir = self.backend.config['local']['media_dir']
        # TODO: check that type is correct.
        file_path = path.uri_to_path(track.uri).split(':', 1)[1]
        file_path = os.path.join(media_dir, file_path)
        track = track.copy(uri=path.path_to_uri(file_path))
        return super(LocalPlaybackProvider, self).change_track(track)
