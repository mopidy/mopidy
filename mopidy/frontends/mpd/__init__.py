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

**Limitations:**

This is a non exhaustive list of MPD features that Mopidy doesn't support.
Items on this list will probably not be supported in the near future.

- Toggling of audio outputs is not supported
- Channels for client-to-client communication are not supported
- Stickers are not supported
- Crossfade is not supported
- Replay gain is not supported
- ``count`` does not provide any statistics
- ``stats`` does not provide any statistics
- ``list`` does not support listing tracks by genre
- ``decoders`` does not provide information about available decoders

The following items are currently not supported, but should be added in the
near future:

- Modifying stored playlists is not supported
- ``tagtypes`` is not supported
- Browsing the file system is not supported
- Live update of the music database is not supported
"""

from __future__ import unicode_literals

# flake8: noqa
from .actor import MpdFrontend
