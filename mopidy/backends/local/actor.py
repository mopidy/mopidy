from __future__ import unicode_literals

import logging
import os

import pykka

from mopidy.backends import base
from mopidy.utils import encoding, path

from .library import LocalLibraryProvider
from .playlists import LocalPlaylistsProvider
from .playback import LocalPlaybackProvider

logger = logging.getLogger('mopidy.backends.local')


class LocalBackend(pykka.ThreadingActor, base.Backend):
    def __init__(self, config, audio):
        super(LocalBackend, self).__init__()

        self.config = config

        self.check_dirs_and_files()

        self.library = LocalLibraryProvider(backend=self)
        self.playback = LocalPlaybackProvider(audio=audio, backend=self)
        self.playlists = LocalPlaylistsProvider(backend=self)

        self.uri_schemes = ['local']

    def check_dirs_and_files(self):
        if not os.path.isdir(self.config['local']['media_dir']):
            logger.warning('Local media dir %s does not exist.' %
                           self.config['local']['media_dir'])

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
