from __future__ import absolute_import, unicode_literals

import logging

import pykka

from mopidy import backend
from mopidy.local import storage
from mopidy.local.library import LocalLibraryProvider
from mopidy.local.playback import LocalPlaybackProvider


logger = logging.getLogger(__name__)


class LocalBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes = ['local']
    libraries = []

    def __init__(self, config, audio):
        super(LocalBackend, self).__init__()

        self.config = config

        storage.check_dirs_and_files(config)

        libraries = dict((l.name, l) for l in self.libraries)
        library_name = config['local']['library']

        if library_name in libraries:
            library = libraries[library_name](config)
            logger.debug('Using %s as the local library', library_name)
        else:
            library = None
            logger.warning('Local library %s not found', library_name)

        self.playback = LocalPlaybackProvider(audio=audio, backend=self)
        self.library = LocalLibraryProvider(backend=self, library=library)
