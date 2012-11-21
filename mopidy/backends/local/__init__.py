"""A backend for playing music from a local music archive.

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

from __future__ import unicode_literals

# flake8: noqa
from .actor import LocalBackend
