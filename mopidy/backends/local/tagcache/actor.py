from __future__ import unicode_literals

import logging

import pykka

from mopidy.backends import base
from mopidy.utils import encoding, path

from .library import LocalTagcacheLibraryProvider

logger = logging.getLogger('mopidy.backends.local.tagcache')


class LocalTagcacheBackend(pykka.ThreadingActor, base.Backend):
    def __init__(self, config, audio):
        super(LocalTagcacheBackend, self).__init__()

        self.config = config
        self.check_dirs_and_files()
        self.library = LocalTagcacheLibraryProvider(backend=self)
        self.uri_schemes = ['local']

    def check_dirs_and_files(self):
        try:
            path.get_or_create_file(self.config['local']['tag_cache_file'])
        except EnvironmentError as error:
            logger.warning(
                'Could not create empty tag cache file: %s',
                encoding.locale_decode(error))
