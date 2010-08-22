************
Installation
************

To get a basic version of Mopidy running, you need Python and the
:doc:`GStreamer library <gstreamer>`. To use Spotify with Mopidy, you also need
:doc:`libspotify and pyspotify <libspotify>`. Mopidy itself can either be
installed from the Python package index, PyPI, or from git.


Install dependencies
====================

.. toctree::
    :hidden:

    gstreamer
    libspotify

Make sure you got the required dependencies installed.

- Python >= 2.6, < 3
- :doc:`GStreamer <gstreamer>` >= 0.10, with Python bindings
- Dependencies for at least one Mopidy mixer:

  - :mod:`mopidy.mixers.alsa` (Linux only)

    - pyalsaaudio >= 0.2 (Debian/Ubuntu package: python-alsaaudio)

  - :mod:`mopidy.mixers.denon` (Linux, OS X, and Windows)

    - pyserial (Debian/Ubuntu package: python-serial)

  - :mod:`mopidy.mixers.nad` (Linux, OS X, and Windows)

    - pyserial (Debian/Ubuntu package: python-serial)

  - :mod:`mopidy.mixers.osa` (OS X only)

    - No additional dependencies.

- Dependencies for at least one Mopidy backend:

  - :mod:`mopidy.backends.libspotify` (Linux, OS X, and Windows)

    - :doc:`libspotify and pyspotify <libspotify>`

  - :mod:`mopidy.backends.local` (Linux, OS X, and Windows)

    - No additional dependencies.


Install latest release
======================

To install the currently latest release of Mopidy using ``pip``::

    sudo aptitude install python-setuptools python-pip   # On Ubuntu/Debian
    sudo brew install pip                                # On OS X
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


Settings
========

Mopidy reads settings from the file ``~/.mopidy/settings.py``, where ``~``
means your *home directory*. If your username is ``alice`` and you are running
Linux, the settings file should probably be at
``/home/alice/.mopidy/settings.py``.

You can either create this file yourself, or run the ``mopidy`` command, and it
will create an empty settings file for you.

Music from Spotify
------------------

If you are using the Spotify backend, which is the default, enter your Spotify
Premium account's username and password into the file, like this::

    SPOTIFY_USERNAME = u'myusername'
    SPOTIFY_PASSWORD = u'mysecret'

Music from local storage
------------------------

If you want use Mopidy to play music you have locally at your machine instead
of using Spotify, you need to change the backend from the default to
:mod:`mopidy.backends.local` by adding the following line to your settings
file::

    BACKENDS = (u'mopidy.backends.local.LocalBackend',)

You may also want to change some of the ``LOCAL_*`` settings. See
:mod:`mopidy.settings`, for a full list of available settings.

Connecting from other machines on the network
---------------------------------------------

As a secure default, Mopidy only accepts connections from ``localhost``. If you
want to open it for connections from other machines on your network, see
the documentation for :attr:`mopidy.settings.MPD_SERVER_HOSTNAME`.


Running Mopidy
==============

To start Mopidy, simply open a terminal and run::

    mopidy

When Mopidy says ``MPD server running at [127.0.0.1]:6600`` it's ready to
accept connections by any MPD client. You can find tons of MPD clients at
http://mpd.wikia.com/wiki/Clients. We use GMPC and ncmpcpp during development.
The first is a GUI client, and the second is a terminal client.

To stop Mopidy, press ``CTRL+C``.
