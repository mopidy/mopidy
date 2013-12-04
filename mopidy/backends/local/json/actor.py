from __future__ import unicode_literals

import logging
import os

import pykka

from mopidy.backends import base
from mopidy.utils import encoding

from . import library

logger = logging.getLogger('mopidy.backends.local.json')


class LocalJsonBackend(pykka.ThreadingActor, base.Backend):
    def __init__(self, config, audio):
        super(LocalJsonBackend, self).__init__()

        self.config = config
        self.library = library.LocalJsonLibraryProvider(backend=self)
        self.uri_schemes = ['local']

        if not os.path.exists(config['local-json']['json_file']):
            try:
                library.write_library(config['local-json']['json_file'], {})
                logger.info('Created empty local JSON library.')
            except EnvironmentError as error:
                error = encoding.locale_decode(error)
                logger.warning('Could not create local library: %s', error)
