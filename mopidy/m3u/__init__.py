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
        schema['base_dir'] = config.Path(optional=True)
        schema['default_encoding'] = config.String()
        schema['default_extension'] = config.String(choices=['.m3u', '.m3u8'])
        schema['playlists_dir'] = config.Path(optional=True)
        return schema

    def setup(self, registry):
        from .backend import M3UBackend
        registry.add('backend', M3UBackend)
