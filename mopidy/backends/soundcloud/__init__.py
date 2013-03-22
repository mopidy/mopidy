"""A backend for playing music from SoundCloud.

This backend handles URIs starting with ``soundcloud:``.

See :ref:`music-from-soundcloud-storage` for further instructions on using this
backend.

**Issues:**

https://github.com/mopidy/mopidy/issues?labels=SoundCloud+backend

**Dependencies:**

.. literalinclude:: ../../../requirements/soundcloud.txt

**Settings:**

- :attr:`mopidy.settings.SOUNDCLOUD_AUTH_TOKEN`
- :attr:`mopidy.settings.SOUNDCLOUD_EXPLORE`
"""

from __future__ import unicode_literals

# flake8: noqa
from .actor import SoundCloudBackend
