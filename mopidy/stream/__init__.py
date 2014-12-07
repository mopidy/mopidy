from __future__ import absolute_import, unicode_literals

import os

import mopidy
from mopidy import config, ext


class Extension(ext.Extension):

    dist_name = 'Mopidy-Stream'
    ext_name = 'stream'
    version = mopidy.__version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['protocols'] = config.List()
        schema['metadata_blacklist'] = config.List(optional=True)
        schema['timeout'] = config.Integer(
            minimum=1000, maximum=1000 * 60 * 60)
        return schema

    def validate_environment(self):
        pass

    def setup(self, registry):
        from .actor import StreamBackend
        registry.add('backend', StreamBackend)
