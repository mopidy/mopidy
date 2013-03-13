"""A backend for playing music from a remote beets music archive.

This backend handles URIs starting with ``beets:``.

See :ref:`music-from-beets-storage` for further instructions on using this
backend.

**Issues:**

https://github.com/mopidy/mopidy/issues?labels=Beets+backend

**Dependencies:**

.. literalinclude:: ../../../requirements/beets.txt

**Settings:**

- :attr:`mopidy.settings.BEETS_SERVER_URI`
"""

from __future__ import unicode_literals

# flake8: noqa
from .actor import BeetsBackend
