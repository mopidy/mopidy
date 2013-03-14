"""A backend for playing music from Soundcloud.

This backend handles URIs starting with ``soundcloud:``.

See :ref:`music-from-soundcloud-storage` for further instructions on using this
backend.

**Issues:**

https://github.com/mopidy/mopidy/issues?labels=Soundcloud+backend

**Dependencies:**

.. literalinclude:: ../../../requirements/soundcloud.txt

**Settings:**

- :attr:`mopidy.settings.SOUNDCLOUD_USERNAME`
"""

from __future__ import unicode_literals

# flake8: noqa
from .actor import SoundcloudBackend
