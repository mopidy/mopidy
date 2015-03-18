from __future__ import absolute_import, unicode_literals

import logging

import pykka

from mopidy import backend
from mopidy.m3u.library import M3ULibraryProvider
from mopidy.m3u.playlists import M3UPlaylistsProvider
from mopidy.utils import encoding, path


logger = logging.getLogger(__name__)


class M3UBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes = ['m3u']

    def __init__(self, config, audio):
        super(M3UBackend, self).__init__()

        self._config = config

        try:
            path.get_or_create_dir(config['m3u']['playlists_dir'])
        except EnvironmentError as error:
            logger.warning(
                'Could not create M3U playlists dir: %s',
                encoding.locale_decode(error))

        self.playlists = M3UPlaylistsProvider(backend=self)
        self.library = M3ULibraryProvider(backend=self)
