"""A backend for playing music for streaming music.

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

from __future__ import unicode_literals

# flake8: noqa
from .actor import StreamBackend
