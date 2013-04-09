from __future__ import unicode_literals

import mopidy
from mopidy import ext
from mopidy.utils import config, formatting


default_config = """
[local]
enabled = true
media_dir = $XDG_MUSIC_DIR
playlists_dir = $XDG_DATA_DIR/mopidy/local/playlists
tag_cache_file = $XDG_DATA_DIR/mopidy/local/tag_cache
"""

__doc__ = """A backend for playing music from a local music archive.

This backend handles URIs starting with ``file:``.

See :ref:`music-from-local-storage` for further instructions on using this
backend.

**Issues**

https://github.com/mopidy/mopidy/issues?labels=Local+backend

**Dependencies**

None

**Configuration**

.. confval:: local/enabled

    If the local extension should be enabled or not.

.. confval:: local/media_dir

    Path to directory with local media files.

.. confval:: local/playlists_dir

    Path to playlists directory with m3u files for local media.

.. confval:: local/tag_cache_file

    Path to tag cache for local media.

**Default config**

.. code-block:: ini

%(config)s
""" % {'config': formatting.indent(default_config)}


class Extension(ext.Extension):

    dist_name = 'Mopidy-Local'
    ext_name = 'local'
    version = mopidy.__version__

    def get_default_config(self):
        return default_config

    def get_config_schema(self):
        schema = config.ExtensionConfigSchema()
        schema['media_dir'] = config.Path()
        schema['playlists_dir'] = config.Path()
        schema['tag_cache_file'] = config.Path()
        return schema

    def validate_environment(self):
        pass

    def get_backend_classes(self):
        from .actor import LocalBackend
        return [LocalBackend]
