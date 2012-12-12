"""A backend for playing music from Spotify

`Spotify <http://www.spotify.com/>`_ is a music streaming service. The backend
uses the official `libspotify
<http://developer.spotify.com/en/libspotify/overview/>`_ library and the
`pyspotify <http://github.com/mopidy/pyspotify/>`_ Python bindings for
libspotify. This backend handles URIs starting with ``spotify:``.

See :ref:`music-from-spotify` for further instructions on using this backend.

.. note::

    This product uses SPOTIFY(R) CORE but is not endorsed, certified or
    otherwise approved in any way by Spotify. Spotify is the registered
    trade mark of the Spotify Group.

**Issues:**

https://github.com/mopidy/mopidy/issues?labels=Spotify+backend

**Dependencies:**

- libspotify >= 12, < 13 (libspotify12 package from apt.mopidy.com)
- pyspotify >= 1.9, < 1.11 (python-spotify package from apt.mopidy.com)

**Settings:**

- :attr:`mopidy.settings.SPOTIFY_CACHE_PATH`
- :attr:`mopidy.settings.SPOTIFY_USERNAME`
- :attr:`mopidy.settings.SPOTIFY_PASSWORD`
"""

from __future__ import unicode_literals

# flake8: noqa
from .actor import SpotifyBackend
