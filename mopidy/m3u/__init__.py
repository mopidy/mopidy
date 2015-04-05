from __future__ import absolute_import, unicode_literals

import logging
import os

import mopidy
from mopidy import config, ext

logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = 'Mopidy-M3U'
    ext_name = 'm3u'
    version = mopidy.__version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['playlists_dir'] = config.Path()
        return schema

    def setup(self, registry):
        from .actor import M3UBackend

        registry.add('backend', M3UBackend)
