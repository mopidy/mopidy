from __future__ import unicode_literals

import mopidy
from mopidy import exceptions, ext
from mopidy.utils import config, formatting


default_config = """
[ext.lastfm]

# If the Last.fm extension should be enabled or not
enabled = true

# Your Last.fm username
username =

# Your Last.fm password
password =
"""

__doc__ = """
Frontend which scrobbles the music you play to your `Last.fm
<http://www.last.fm>`_ profile.

.. note::

    This frontend requires a free user account at Last.fm.

**Dependencies**

.. literalinclude:: ../../../requirements/lastfm.txt

**Default config**

.. code-block:: ini

%(config)s

**Usage**

The frontend is enabled by default if all dependencies are available.
""" % {'config': formatting.indent(default_config)}


class Extension(ext.Extension):

    dist_name = 'Mopidy-Lastfm'
    ext_name = 'lastfm'
    version = mopidy.__version__

    def get_default_config(self):
        return default_config

    def get_config_schema(self):
        schema = config.ExtensionConfigSchema()
        schema['username'] = config.String()
        schema['password'] = config.String(secret=True)
        return schema

    def validate_environment(self):
        try:
            import pylast  # noqa
        except ImportError as e:
            raise exceptions.ExtensionError('pylast library not found', e)

    def get_frontend_classes(self):
        from .actor import LastfmFrontend
        return [LastfmFrontend]
