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

  - *Default:* :mod:`mopidy.mixers.gstreamer_software` (Linux, OS X, and
    Windows)

    - No additional dependencies.

  - :mod:`mopidy.mixers.nad` (Linux, OS X, and Windows)

    - pyserial (Debian/Ubuntu package: python-serial)

  - :mod:`mopidy.mixers.osa` (OS X only)

    - No additional dependencies.

- Dependencies for at least one Mopidy backend:

  - *Default:* :mod:`mopidy.backends.libspotify` (Linux, OS X, and Windows)

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

Next, you need to set a couple of :doc:`settings </settings>`, and then you're
ready to :doc:`run Mopidy </running>`.


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

Next, you need to set a couple of :doc:`settings </settings>`, and then you're
ready to :doc:`run Mopidy </running>`.
