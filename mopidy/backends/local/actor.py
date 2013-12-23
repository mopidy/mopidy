from __future__ import unicode_literals

import logging
import os

import pykka

from mopidy.backends import base
from mopidy.utils import encoding, path

from .json import JsonLibrary
from .library import LocalLibraryProvider
from .playback import LocalPlaybackProvider
from .playlists import LocalPlaylistsProvider

logger = logging.getLogger('mopidy.backends.local')


class LocalBackend(pykka.ThreadingActor, base.Backend):
    uri_schemes = ['local']

    def __init__(self, config, audio):
        super(LocalBackend, self).__init__()

        self.config = config

        self.check_dirs_and_files()

        # TODO: move to getting this from registry
        library = JsonLibrary(config)

        self.playback = LocalPlaybackProvider(audio=audio, backend=self)
        self.playlists = LocalPlaylistsProvider(backend=self)
        self.library = LocalLibraryProvider(backend=self, library=library)

    def check_dirs_and_files(self):
        if not os.path.isdir(self.config['local']['media_dir']):
            logger.warning('Local media dir %s does not exist.' %
                           self.config['local']['media_dir'])

        try:
            path.get_or_create_dir(self.config['local']['data_dir'])
        except EnvironmentError as error:
            logger.warning(
                'Could not create local data dir: %s',
                encoding.locale_decode(error))

        # TODO: replace with data dir?
        try:
            path.get_or_create_dir(self.config['local']['playlists_dir'])
        except EnvironmentError as error:
            logger.warning(
                'Could not create local playlists dir: %s',
                encoding.locale_decode(error))
