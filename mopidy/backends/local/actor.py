from __future__ import unicode_literals

import logging

import pykka

from mopidy.backends import base
from mopidy.utils import encoding, path

from .library import LocalLibraryProvider
from .playlists import LocalPlaylistsProvider

logger = logging.getLogger('mopidy.backends.local')


class LocalBackend(pykka.ThreadingActor, base.Backend):
    def __init__(self, config, audio):
        super(LocalBackend, self).__init__()

        self.config = config

        self.create_dirs_and_files()

        self.library = LocalLibraryProvider(backend=self)
        self.playback = base.BasePlaybackProvider(audio=audio, backend=self)
        self.playlists = LocalPlaylistsProvider(backend=self)

        self.uri_schemes = ['file']

    def create_dirs_and_files(self):
        try:
            path.get_or_create_dir(self.config['local']['media_dir'])
        except EnvironmentError as error:
            logger.warning(
                'Could not create local media dir: %s',
                encoding.locale_decode(error))

        try:
            path.get_or_create_dir(self.config['local']['playlists_dir'])
        except EnvironmentError as error:
            logger.warning(
                'Could not create local playlists dir: %s',
                encoding.locale_decode(error))

        try:
            path.get_or_create_file(self.config['local']['tag_cache_file'])
        except EnvironmentError as error:
            logger.warning(
                'Could not create empty tag cache file: %s',
                encoding.locale_decode(error))
