************
Installation
************

Mopidy itself is a breeze to install, as it just requires a standard Python
2.6 or newer installation. The libraries we depend on to connect to the Spotify
service is far more tricky to get working for the time being. Until
installation of these libraries are either well documented by their developers,
or the libraries are packaged for various Linux distributions, we will supply
our own installation guides.


Dependencies
============

.. toctree::
    :hidden:

    despotify
    libspotify

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


Install latest release
======================

To install the currently latest release of Mopidy using ``pip``::

    sudo aptitude install python-pip                # On Ubuntu/Debian
    sudo brew install pip                           # On OS X
    sudo pip install Mopidy

To later upgrade to the latest release::

    sudo pip install -U Mopidy

If you for some reason can't use ``pip``, try ``easy_install``.


Install development version
===========================

If you want to follow Mopidy development closer, you may install the
development version of Mopidy::

    sudo aptitude install git-core                  # On Ubuntu/Debian
    sudo brew install git                           # On OS X
    git clone git://github.com/jodal/mopidy.git
    cd mopidy/
    sudo python setup.py install

To later update to the very latest version::

    cd mopidy/
    git pull
    sudo python setup.py install

For an introduction to ``git``, please visit `git-scm.com
<http://git-scm.com/>`_.


Spotify settings
================

Create a file named ``settings.py`` in the directory ``~/.mopidy/``. Enter
your Spotify Premium account's username and password into the file, like this::

    SPOTIFY_USERNAME = u'myusername'
    SPOTIFY_PASSWORD = u'mysecret'

For a full list of available settings, see :mod:`mopidy.settings`.


Running Mopidy
==============

To start Mopidy, simply open a terminal and run::

    mopidy

When Mopidy says ``MPD server running at [localhost]:6600`` it's ready to
accept connections by any MPD client. You can find a list of tons of MPD
clients at http://mpd.wikia.com/wiki/Clients. We use Sonata, GMPC, ncmpc, and
ncmpcpp during development. The first two are GUI clients, while the last two
are terminal clients.

To stop Mopidy, press ``CTRL+C``.
