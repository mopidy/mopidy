from __future__ import unicode_literals

import logging

import pykka

from mopidy.backends import base
from mopidy.utils import encoding, path

from .library import LocalJsonLibraryProvider

logger = logging.getLogger('mopidy.backends.local.json')


class LocalJsonBackend(pykka.ThreadingActor, base.Backend):
    def __init__(self, config, audio):
        super(LocalJsonBackend, self).__init__()

        self.config = config
        self.check_dirs_and_files()
        self.library = LocalJsonLibraryProvider(backend=self)
        self.uri_schemes = ['local']

    def check_dirs_and_files(self):
        try:
            path.get_or_create_file(self.config['local-json']['json_file'])
        except EnvironmentError as error:
            logger.warning(
                'Could not create empty json file: %s',
                encoding.locale_decode(error))
