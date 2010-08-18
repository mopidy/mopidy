************
Installation
************

To get a basic version of Mopidy running, you need Python and the GStreamer
library. To use Spotify with Mopidy, you also need :doc:`libspotify and
pyspotify <libspotify>`. Mopidy itself can either be installed from the Python
package index, PyPI, or from git.


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

Create a file named ``settings.py`` in the directory ``~/.mopidy/``.

If you are using a Spotify backend, enter your Spotify Premium account's
username and password into the file, like this::

    SPOTIFY_USERNAME = u'myusername'
    SPOTIFY_PASSWORD = u'mysecret'

Currently :mod:`mopidy.backends.libspotify` is the default backend. If you want
to use :mod:`mopidy.backends.local`, add the following setting::

    BACKENDS = (u'mopidy.backends.local.LocalBackend',)

For a full list of available settings, see :mod:`mopidy.settings`.


Running Mopidy
==============

To start Mopidy, simply open a terminal and run::

    mopidy

When Mopidy says ``MPD server running at [localhost]:6600`` it's ready to
accept connections by any MPD client. You can find a list of tons of MPD
clients at http://mpd.wikia.com/wiki/Clients. We use GMPC and
ncmpcpp during development. The first is a GUI client, and the second is a
terminal client.

To stop Mopidy, press ``CTRL+C``.
