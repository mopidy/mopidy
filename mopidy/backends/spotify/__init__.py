from __future__ import unicode_literals

import mopidy
from mopidy import config, exceptions, ext
from mopidy.utils import formatting


default_config = """
[spotify]
enabled = true
username =
password =
bitrate = 160
timeout = 10
cache_dir = $XDG_CACHE_DIR/mopidy/spotify
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

**Configuration**

.. confval:: spotify/enabled

    If the Spotify extension should be enabled or not.

.. confval:: spotify/username

    Your Spotify Premium username.

.. confval:: spotify/password

    Your Spotify Premium password.

.. confval:: spotify/bitrate

    The preferred audio bitrate. Valid values are 96, 160, 320.

.. confval:: spotify/timeout

    Max number of seconds to wait for Spotify operations to complete.

.. confval:: spotify/cache_dir

    Path to the Spotify data cache. Cannot be shared with other Spotify apps.

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
        schema['cache_dir'] = config.Path()
        return schema

    def validate_environment(self):
        try:
            import spotify  # noqa
        except ImportError as e:
            raise exceptions.ExtensionError('pyspotify library not found', e)

    def get_backend_classes(self):
        from .actor import SpotifyBackend
        return [SpotifyBackend]
