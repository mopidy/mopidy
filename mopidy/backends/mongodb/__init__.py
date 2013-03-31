"""A backend for playing music from a local music archive whose metadata is
stored in a MongoDB instance.

This backend handles URIs starting with ``file:``.

See :ref:`music-from-mongodb` for further instructions on using this
backend.

**Issues:**

https://github.com/mopidy/mopidy/issues?labels=MongoDB+backend

**Dependencies:**

- None

**Settings:**

- :attr:`mopidy.settings.MONGODB_URL`
"""

from __future__ import unicode_literals

# flake8: noqa
from .actor import MongoDBBackend
