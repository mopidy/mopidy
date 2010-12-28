***********************
libspotify installation
***********************

Mopidy uses `libspotify
<http://developer.spotify.com/en/libspotify/overview/>`_ for playing music from
the Spotify music service. To use :mod:`mopidy.backends.libspotify` you must
install libspotify and `pyspotify <http://github.com/mopidy/pyspotify>`_.

.. warning::

    This backend requires a `Spotify premium account
    <http://www.spotify.com/no/get-spotify/premium/>`_.

.. note::

    This product uses SPOTIFY CORE but is not endorsed, certified or otherwise
    approved in any way by Spotify. Spotify is the registered trade mark of the
    Spotify Group.


Installing libspotify on Linux
==============================

Download and install libspotify 0.0.6 for your OS and CPU architecture from
https://developer.spotify.com/en/libspotify/.

For 64-bit Linux the process is as follows::

    wget http://developer.spotify.com/download/libspotify/libspotify-0.0.6-linux6-x86_64.tar.gz
    tar zxfv libspotify-0.0.6-linux6-x86_64.tar.gz
    cd libspotify-0.0.6-linux6-x86_64/
    sudo make install prefix=/usr/local
    sudo ldconfig

When libspotify has been installed, continue with
:ref:`pyspotify_installation`.


Installing libspotify on OS X
=============================

In OS X you need to have `XCode <http://developer.apple.com/tools/xcode/>`_ and
`Homebrew <http://mxcl.github.com/homebrew/>`_ installed. Then, to install
libspotify::

    brew install libspotify

To update your existing libspotify installation using Homebrew::

    brew update
    brew install `brew outdated`

When libspotify has been installed, continue with
:ref:`pyspotify_installation`.


Install libspotify on Windows
=============================

**TODO** Test and document installation on Windows.


.. _pyspotify_installation:

Installing pyspotify
====================

Install pyspotify's dependencies. At Debian/Ubuntu systems::

    sudo aptitude install python-dev

In OS X no additional dependencies are needed.

Check out the pyspotify code, and install it::

    wget --no-check-certificate -O pyspotify.tar.gz https://github.com/mopidy/pyspotify/tarball/mopidy
    tar zxfv pyspotify.tar.gz
    cd pyspotify/pyspotify/
    sudo python setup.py install
