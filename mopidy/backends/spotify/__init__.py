from __future__ import unicode_literals

import os

import mopidy
from mopidy import ext
from mopidy.exceptions import ExtensionError
from mopidy.utils import config


class Extension(ext.Extension):

    dist_name = 'Mopidy-Spotify'
    ext_name = 'spotify'
    version = mopidy.__version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return open(conf_file).read()

    def get_config_schema(self):
        schema = config.ExtensionConfigSchema()
        schema['username'] = config.String()
        schema['password'] = config.String(secret=True)
        schema['bitrate'] = config.Integer(choices=(96, 160, 320))
        schema['timeout'] = config.Integer(minimum=0)
        schema['cache_dir'] = config.Path()
        return schema

    def validate_environment(self):
        try:
            import spotify  # noqa
        except ImportError as e:
            raise ExtensionError('pyspotify library not found', e)

    def get_backend_classes(self):
        from .actor import SpotifyBackend
        return [SpotifyBackend]
