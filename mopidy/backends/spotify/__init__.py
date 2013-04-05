from __future__ import unicode_literals

import mopidy
from mopidy import ext
from mopidy.exceptions import ExtensionError
from mopidy.utils import config, formatting


default_config = """
[spotify]

# If the Spotify extension should be enabled or not
enabled = true

# Your Spotify Premium username
username =

# Your Spotify Premium password
password =

# The preferred audio bitrate. Valid values are 96, 160, 320
bitrate = 160

# Max number of seconds to wait for Spotify operations to complete
timeout = 10

# Path to the Spotify data cache. Cannot be shared with other Spotify apps
cache_path = $XDG_CACHE_DIR/mopidy/spotify

# Connect to Spotify through a proxy
proxy_hostname =
proxy_username =
proxy_password =
"""

__doc__ = """A backend for playing music from Spotify

`Spotify <http://www.spotify.com/>`_ is a music streaming service. The backend
uses the official `libspotify
<http://developer.spotify.com/en/libspotify/overview/>`_ library and the
`pyspotify <http://github.com/mopidy/pyspotify/>`_ Python bindings for
libspotify. This backend handles URIs starting with ``spotify:``.

See :ref:`music-from-spotify` for further instructions on using this backend.

.. note::

    This product uses SPOTIFY(R) CORE but is not endorsed, certified or
    otherwise approved in any way by Spotify. Spotify is the registered
    trade mark of the Spotify Group.

**Issues**

https://github.com/mopidy/mopidy/issues?labels=Spotify+backend

**Dependencies**

.. literalinclude:: ../../../requirements/spotify.txt

**Default config**

.. code-block:: ini

%(config)s
""" % {'config': formatting.indent(default_config)}


class Extension(ext.Extension):

    dist_name = 'Mopidy-Spotify'
    ext_name = 'spotify'
    version = mopidy.__version__

    def get_default_config(self):
        return default_config

    def get_config_schema(self):
        schema = config.ExtensionConfigSchema()
        schema['username'] = config.String()
        schema['password'] = config.String(secret=True)
        schema['bitrate'] = config.Integer(choices=(96, 160, 320))
        schema['timeout'] = config.Integer(minimum=0)
        schema['cache_path'] = config.Path()
        schema['proxy_hostname'] = config.Hostname(optional=True)
        schema['proxy_username'] = config.String(optional=True)
        schema['proxy_password'] = config.String(optional=True, secret=True)
        return schema

    def validate_environment(self):
        try:
            import spotify  # noqa
        except ImportError as e:
            raise ExtensionError('pyspotify library not found', e)

    def get_backend_classes(self):
        from .actor import SpotifyBackend
        return [SpotifyBackend]
