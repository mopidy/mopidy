from __future__ import unicode_literals

import mopidy
from mopidy import ext
from mopidy.utils import config, formatting


default_config = """
[ext.local]

# If the local extension should be enabled or not
enabled = true

# Path to folder with local music
music_path = $XDG_MUSIC_DIR

# Path to playlist folder with m3u files for local music
playlist_path = $XDG_DATA_DIR/mopidy/playlists

# Path to tag cache for local music
tag_cache_file = $XDG_DATA_DIR/mopidy/tag_cache
"""

__doc__ = """A backend for playing music from a local music archive.

This backend handles URIs starting with ``file:``.

See :ref:`music-from-local-storage` for further instructions on using this
backend.

**Issues:**

https://github.com/mopidy/mopidy/issues?labels=Local+backend

**Dependencies:**

- None

**Default config:**

.. code-block:: ini

%(config)s
""" % {'config': formatting.indent(default_config)}


class Extension(ext.Extension):

    name = 'Mopidy-Local'
    version = mopidy.__version__

    def get_default_config(self):
        return default_config

    def get_config_schema(self):
        schema = config.ExtensionConfigSchema()
        schema['music_path'] = config.String()
        schema['playlist_path'] = config.String()
        schema['tag_cache_file'] = config.String()

    def validate_environment(self):
        pass

    def get_backend_classes(self):
        from .actor import LocalBackend
        return [LocalBackend]
