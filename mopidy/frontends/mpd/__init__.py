"""The MPD server frontend.

MPD stands for Music Player Daemon. MPD is an independent project and server.
Mopidy implements the MPD protocol, and is thus compatible with clients for the
original MPD server.

**Dependencies:**

- None

**Settings:**

- :attr:`mopidy.settings.MPD_SERVER_HOSTNAME`
- :attr:`mopidy.settings.MPD_SERVER_PORT`
- :attr:`mopidy.settings.MPD_SERVER_PASSWORD`

**Usage:**

Make sure :attr:`mopidy.settings.FRONTENDS` includes
``mopidy.frontends.mpd.MpdFrontend``. By default, the setting includes the MPD
frontend.
"""

from __future__ import unicode_literals

# flake8: noqa
from .actor import MpdFrontend
