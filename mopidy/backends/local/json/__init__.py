from __future__ import unicode_literals

import os

import mopidy
from mopidy import config, ext


class Extension(ext.Extension):

    dist_name = 'Mopidy-Local-JSON'
    ext_name = 'local-json'
    version = mopidy.__version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['json_file'] = config.Path()
        return schema

    def get_backend_classes(self):
        from .actor import LocalJsonBackend
        return [LocalJsonBackend]

    def get_library_updaters(self):
        from .library import LocalJsonLibraryUpdateProvider
        return [LocalJsonLibraryUpdateProvider]
