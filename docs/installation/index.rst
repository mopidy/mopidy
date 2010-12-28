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

- GStreamer >= 0.10, with Python bindings. See :doc:`gstreamer`.

- Mixer dependencies: The default mixer does not require any additional
  dependencies. If you use another mixer, see the mixer's docs for any
  additional requirements.

- Dependencies for at least one Mopidy backend:

  - The default backend, :mod:`mopidy.backends.libspotify`, requires libspotify
    and pyspotify. See :doc:`libspotify`.

  - The local backend, :mod:`mopidy.backends.local`, requires no additional
    dependencies.

- Optional dependencies:

  - To use the Last.FM scrobbler, see :mod:`mopidy.frontends.lastfm` for
    additional requirements.


Install latest stable release
=============================

To install the currently latest stable release of Mopidy using ``pip``::

    sudo aptitude install python-setuptools python-pip   # On Ubuntu/Debian
    sudo brew install pip                                # On OS X
    sudo pip install -U Mopidy

To later upgrade to the latest release, just rerun the last command.

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


Track development using Git
===========================

If you want to contribute to Mopidy, you should install Mopidy using Git::

    sudo aptitude install git-core                  # On Ubuntu/Debian
    sudo brew install git                           # On OS X
    git clone git://github.com/mopidy/mopidy.git

You can then run Mopidy directly from the Git repository::

    cd mopidy/          # Move into the Git repo dir
    python mopidy       # Run python on the mopidy source code dir

To get the latest changes to Mopidy::

    cd mopidy/
    git pull

For an introduction to ``git``, please visit `git-scm.com
<http://git-scm.com/>`_. Also, please read our :doc:`developer documentation
</development/index>`.
