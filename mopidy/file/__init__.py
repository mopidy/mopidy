from __future__ import absolute_import, unicode_literals

import logging
import os

import mopidy
from mopidy import config, ext

logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = 'Mopidy-File'
    ext_name = 'file'
    version = mopidy.__version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['media_dirs'] = config.List(optional=True)
        schema['excluded_file_extensions'] = config.List(optional=True)
        schema['show_dotfiles'] = config.Boolean(optional=True)
        schema['follow_symlinks'] = config.Boolean(optional=True)
        schema['metadata_timeout'] = config.Integer(optional=True)
        return schema

    def setup(self, registry):
        from .backend import FileBackend
        registry.add('backend', FileBackend)
