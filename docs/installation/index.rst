************
Installation
************

Mopidy itself is a breeze to install, as it just requires a standard Python
installation. The libraries we depend on to connect to the Spotify service is
far more tricky to get working for the time being. Until installation of these
libraries are either well documented by their developers, or the libraries are
packaged for various Linux distributions, we will supply our own installation
guides here.

.. toctree::
    :maxdepth: 1

    despotify
    libspotify


Dependencies
============

- Python >= 2.6
- Dependencies for at least one Mopidy mixer:

  - AlsaMixer (Linux only)

    - pyalsaaudio >= 0.2 (Debian/Ubuntu package: python-alsaaudio)

  - OsaMixer (OS X only)

    - Nothing needed.

- Dependencies for at least one Mopidy backend:

  - DespotifyBackend (Linux and OS X)

    - see :doc:`despotify`

  - LibspotifyBackend (Linux only)

    - see :doc:`libspotify`


Spotify settings
================

Create a file named ``local.py`` in the directory ``mopidy/settings/``. Enter
your Spotify Premium account's username and password into the file, like this::

    SPOTIFY_USERNAME = u'myusername'
    SPOTIFY_PASSWORD = u'mysecret'


Switching backend
=================

Currently the despotify backend is the default. If you want to use the
libspotify backend instead, copy the Spotify application key to
``mopidy/spotify_appkey.key``, and add the following to
``mopidy/mopidy/settings/local.py``::

    BACKENDS = (u'mopidy.backends.libspotify.LibspotifyBackend',)

For a full list of available settings, see :mod:`mopidy.settings.default`.


Running Mopidy
==============

To start Mopidy, go to the root of the Mopidy project, then simply run::

    python mopidy

When Mopidy says ``Please connect to localhost port 6600 using an MPD client.``
it's ready to accept connections by any MPD client. You can find a list of tons
of MPD clients at http://mpd.wikia.com/wiki/Clients. We use Sonata, GMPC,
ncmpc, and ncmpcpp during development. The first two are GUI clients, while the
last two are terminal clients.

To stop Mopidy, press ``CTRL+C``.
