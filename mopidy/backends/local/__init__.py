from __future__ import unicode_literals

import mopidy
from mopidy import ext


__doc__ = """A backend for playing music from a local music archive.

This backend handles URIs starting with ``file:``.

See :ref:`music-from-local-storage` for further instructions on using this
backend.

**Issues:**

https://github.com/mopidy/mopidy/issues?labels=Local+backend

**Dependencies:**

- None

**Settings:**

- :attr:`mopidy.settings.LOCAL_MUSIC_PATH`
- :attr:`mopidy.settings.LOCAL_PLAYLIST_PATH`
- :attr:`mopidy.settings.LOCAL_TAG_CACHE_FILE`
"""


class Extension(ext.Extension):

    name = 'Mopidy-Local'
    version = mopidy.__version__

    def get_default_config(self):
        return '[ext.local]'

    def validate_config(self, config):
        pass

    def validate_environment(self):
        pass

    def get_backend_classes(self):
        from .actor import LocalBackend
        return [LocalBackend]
