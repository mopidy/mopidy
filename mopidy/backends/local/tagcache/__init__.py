from __future__ import unicode_literals

import os

import mopidy
from mopidy import config, ext


class Extension(ext.Extension):

    dist_name = 'Mopidy-Local-Tagcache'
    ext_name = 'local-tagcache'
    version = mopidy.__version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    # Config only contains local-tagcache/enabled since we are not setting our
    # own schema.

    def get_backend_classes(self):
        from .actor import LocalTagcacheBackend
        return [LocalTagcacheBackend]

    def get_library_updaters(self):
        from .library import LocalTagcacheLibraryUpdateProvider
        return [LocalTagcacheLibraryUpdateProvider]
