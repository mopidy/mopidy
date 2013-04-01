from __future__ import unicode_literals

import mopidy
from mopidy import ext
from mopidy.utils import config, formatting


default_config = """
[ext.mpd]

# If the MPD extension should be enabled or not
enabled = true

# Which address the MPD server should bind to
#
# 127.0.0.1
#     Listens only on the IPv4 loopback interface
# ::1
#     Listens only on the IPv6 loopback interface
# 0.0.0.0
#     Listens on all IPv4 interfaces
# ::
#     Listens on all interfaces, both IPv4 and IPv6
hostname = 127.0.0.1

# Which TCP port the MPD server should listen to
port = 6600

# The password required for connecting to the MPD server
password =

# The maximum number of concurrent connections the MPD server will accept
max_connections = 20

# Number of seconds an MPD client can stay inactive before the connection is
# closed by the server
connection_timeout = 60
"""

__doc__ = """The MPD server frontend.

MPD stands for Music Player Daemon. MPD is an independent project and server.
Mopidy implements the MPD protocol, and is thus compatible with clients for the
original MPD server.

**Dependencies:**

- None

**Default config:**

.. code-block:: ini

%(config)s

**Usage:**

The frontend is enabled by default.

**Limitations:**

This is a non exhaustive list of MPD features that Mopidy doesn't support.
Items on this list will probably not be supported in the near future.

- Toggling of audio outputs is not supported
- Channels for client-to-client communication are not supported
- Stickers are not supported
- Crossfade is not supported
- Replay gain is not supported
- ``count`` does not provide any statistics
- ``stats`` does not provide any statistics
- ``list`` does not support listing tracks by genre
- ``decoders`` does not provide information about available decoders

The following items are currently not supported, but should be added in the
near future:

- Modifying stored playlists is not supported
- ``tagtypes`` is not supported
- Browsing the file system is not supported
- Live update of the music database is not supported
""" % {'config': formatting.indent(default_config)}


class Extension(ext.Extension):

    name = 'Mopidy-MPD'
    version = mopidy.__version__

    def get_default_config(self):
        return default_config

    def get_config_schema(self):
        schema = config.ExtensionConfigSchema()
        schema['hostname'] = config.Hostname()
        schema['port'] = config.Port()
        schema['password'] = config.String(optional=True, secret=True)
        schema['max_connections'] = config.Integer(minimum=1)
        schema['connection_timeout'] = config.Integer(minimum=1)
        return schema

    def validate_environment(self):
        pass

    def get_frontend_classes(self):
        from .actor import MpdFrontend
        return [MpdFrontend]
