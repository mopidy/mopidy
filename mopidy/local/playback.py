from __future__ import absolute_import, unicode_literals

from mopidy import backend
from mopidy.local import translator


class LocalPlaybackProvider(backend.PlaybackProvider):

    def translate_uri(self, uri):
        return translator.local_uri_to_file_uri(
            uri, self.backend.config['local']['media_dir'])
