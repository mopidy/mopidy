from __future__ import unicode_literals

import os

import mopidy
from mopidy import config, ext


class Extension(ext.Extension):

    dist_name = 'Mopidy-Local'
    ext_name = 'local'
    version = mopidy.__version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['media_dir'] = config.Path()
        schema['playlists_dir'] = config.Path()
        schema['tag_cache_file'] = config.Path()
        schema['scan_timeout'] = config.Integer(
            minimum=1000, maximum=1000*60*60)
        schema['excluded_file_extensions'] = config.List(optional=True)
        return schema

    def validate_environment(self):
        pass

    def get_backend_classes(self):
        from .actor import LocalBackend
        return [LocalBackend]

    def get_library_updaters(self):
        from .library import LocalLibraryUpdateProvider
        return [LocalLibraryUpdateProvider]
