from __future__ import absolute_import, unicode_literals

import os

import mopidy
from mopidy import config, ext


class Extension(ext.Extension):

    dist_name = 'Mopidy-SoftwareMixer'
    ext_name = 'softwaremixer'
    version = mopidy.__version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        return schema

    def setup(self, registry):
        from .mixer import SoftwareMixer
        registry.add('mixer', SoftwareMixer)
