from __future__ import unicode_literals

import mopidy
from mopidy import ext


__doc__ = """A backend for playing music for streaming music.

This backend will handle streaming of URIs in
:attr:`mopidy.settings.STREAM_PROTOCOLS` assuming the right plugins are
installed.

**Issues:**

https://github.com/mopidy/mopidy/issues?labels=Stream+backend

**Dependencies:**

- None

**Settings:**

- :attr:`mopidy.settings.STREAM_PROTOCOLS`
"""


class Extension(ext.Extension):

    name = 'Mopidy-Stream'
    version = mopidy.__version__

    def get_default_config(self):
        return '[ext.stream]'

    def validate_config(self, config):
        pass

    def validate_environment(self):
        pass

    def get_backend_classes(self):
        from .actor import StreamBackend
        return [StreamBackend]
