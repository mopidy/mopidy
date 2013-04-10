from __future__ import unicode_literals

import mopidy
from mopidy import config, ext
from mopidy.utils import formatting


default_config = """
[stream]
enabled = true
protocols =
    http
    https
    mms
    rtmp
    rtmps
    rtsp
"""

__doc__ = """
A backend for playing music for streaming music.

This backend will handle streaming of URIs matching the
:confval:`stream/protocols` config value, assuming the needed GStreamer plugins
are installed.

**Issues**

https://github.com/mopidy/mopidy/issues?labels=Stream+backend

**Dependencies**

None

**Configuration**

.. confval:: stream/enabled

    If the stream extension should be enabled or not.

.. confval:: stream/protocols

    Whitelist of URI schemas to allow streaming from.

**Default config**

.. code-block:: ini

%(config)s
""" % {'config': formatting.indent(default_config)}


class Extension(ext.Extension):

    dist_name = 'Mopidy-Stream'
    ext_name = 'stream'
    version = mopidy.__version__

    def get_default_config(self):
        return default_config

    def get_config_schema(self):
        schema = config.ExtensionConfigSchema()
        schema['protocols'] = config.List()
        return schema

    def validate_environment(self):
        pass

    def get_backend_classes(self):
        from .actor import StreamBackend
        return [StreamBackend]
