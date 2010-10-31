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

- Optional dependencies:

  - :mod:`mopidy.frontends.lastfm`

    - pylast >= 4.3.0


Install latest release
======================

To install the currently latest release of Mopidy using ``pip``::

    sudo aptitude install python-setuptools python-pip   # On Ubuntu/Debian
    sudo brew install pip                                # On OS X
    sudo pip install mopidy

To later upgrade to the latest release::

    sudo pip install -U mopidy

If you for some reason can't use ``pip``, try ``easy_install``.

Next, you need to set a couple of :doc:`settings </settings>`, and then you're
ready to :doc:`run Mopidy </running>`.


Install development snapshot
============================

If you want to follow Mopidy development closer, you may install a snapshot of
Mopidy's ``develop`` branch::

    sudo aptitude install python-setuptools python-pip   # On Ubuntu/Debian
    sudo brew install pip                                # On OS X
    sudo pip install mopidy==dev

Next, you need to set a couple of :doc:`settings </settings>`, and then you're
ready to :doc:`run Mopidy </running>`.


Run from source code checkout
=============================

If you may want to contribute to Mopidy, and want access to other branches as
well, you can checkout the Mopidy source from Git and run it directly from the
ckeckout::

    sudo aptitude install git-core                  # On Ubuntu/Debian
    sudo brew install git                           # On OS X
    git clone git://github.com/jodal/mopidy.git
    cd mopidy/
    python mopidy                                   # Yes, 'mopidy' is a dir

To later update to the very latest version::

    cd mopidy/
    git pull

For an introduction to ``git``, please visit `git-scm.com
<http://git-scm.com/>`_. Also, please read our :doc:`developer documentation
</development/index>`.
