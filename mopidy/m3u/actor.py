from __future__ import absolute_import, unicode_literals

import logging

import pykka

from mopidy import backend, m3u
from mopidy.internal import encoding, path
from mopidy.m3u.library import M3ULibraryProvider
from mopidy.m3u.playlists import M3UPlaylistsProvider


logger = logging.getLogger(__name__)


class M3UBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes = ['m3u']

    def __init__(self, config, audio):
        super(M3UBackend, self).__init__()

        self._config = config

        if config['m3u']['playlists_dir'] is not None:
            self._playlists_dir = config['m3u']['playlists_dir']
            try:
                path.get_or_create_dir(self._playlists_dir)
            except EnvironmentError as error:
                logger.warning(
                    'Could not create M3U playlists dir: %s',
                    encoding.locale_decode(error))
        else:
            self._playlists_dir = m3u.Extension.get_data_dir(config)

        self.playlists = M3UPlaylistsProvider(backend=self)
        self.library = M3ULibraryProvider(backend=self)
