from __future__ import unicode_literals

import logging
import os

import mopidy
from mopidy import config, ext
from mopidy.utils import encoding, path

logger = logging.getLogger(__name__)


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
        schema['tag_cache_file'] = config.Deprecated()
        schema['scan_timeout'] = config.Integer(
            minimum=1000, maximum=1000*60*60)
        schema['excluded_file_extensions'] = config.List(optional=True)
        return schema

    def validate_environment(self):
        try:
            path.get_or_create_dir(b'$XDG_DATA_DIR/mopidy/local')
        except EnvironmentError as error:
            error = encoding.locale_decode(error)
            logger.warning('Could not create local data dir: %s', error)

    def get_backend_classes(self):
        from .actor import LocalBackend
        return [LocalBackend]

    def get_command(self):
        from .commands import LocalCommand
        return LocalCommand()
