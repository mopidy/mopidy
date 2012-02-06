***********************
libspotify installation
***********************

Mopidy uses `libspotify
<http://developer.spotify.com/en/libspotify/overview/>`_ for playing music from
the Spotify music service. To use :mod:`mopidy.backends.spotify` you must
install libspotify and `pyspotify <http://pyspotify.mopidy.com/>`_.

.. note::

    This backend requires a paid `Spotify premium account
    <http://www.spotify.com/no/get-spotify/premium/>`_.


Installing libspotify
=====================


On Linux from APT archive
-------------------------

If you install from APT, jump directly to :ref:`pyspotify_installation` below.


On Linux from source
--------------------

First, check pyspotify's changelog to see what's the latest version of
libspotify which is supported. The versions of libspotify and pyspotify are
tightly coupled.

Download and install the appropriate version of libspotify for your OS and CPU
architecture from https://developer.spotify.com/en/libspotify/.

For libspotify 0.0.8 for 64-bit Linux the process is as follows::

    wget http://developer.spotify.com/download/libspotify/libspotify-0.0.8-linux6-x86_64.tar.gz
    tar zxfv libspotify-0.0.8-linux6-x86_64.tar.gz
    cd libspotify-0.0.8-linux6-x86_64/
    sudo make install prefix=/usr/local
    sudo ldconfig

Remember to adjust for the latest libspotify version supported by pyspotify,
your OS and your CPU architecture.

When libspotify has been installed, continue with
:ref:`pyspotify_installation`.


On OS X from Homebrew
---------------------

In OS X you need to have `XCode <http://developer.apple.com/tools/xcode/>`_ and
`Homebrew <http://mxcl.github.com/homebrew/>`_ installed. Then, to install
libspotify::

    brew install libspotify

To update your existing libspotify installation using Homebrew::

    brew update
    brew upgrade

When libspotify has been installed, continue with
:ref:`pyspotify_installation`.


.. _pyspotify_installation:

Installing pyspotify
====================

When you've installed libspotify, it's time for making it available from Python
by installing pyspotify.


On Linux from APT archive
-------------------------

If you run a Debian based Linux distribution, like Ubuntu, see
http://apt.mopidy.com/ for how to use the Mopidy APT archive as a software
source on your system. Then, simply run::

    sudo apt-get install python-spotify

This command will install both libspotify and pyspotify for you.


On Linux from source
-------------------------

If you have have already installed libspotify, you can continue with installing
the libspotify Python bindings, called pyspotify.

On Linux, you need to get the Python development files installed. On
Debian/Ubuntu systems run::

    sudo apt-get install python-dev

Then get, build, and install the latest releast of pyspotify using ``pip``::

    sudo pip install -U pyspotify


On OS X from source
-------------------

If you have already installed libspotify, you can get, build, and install the
latest releast of pyspotify using ``pip``::

    sudo pip install -U pyspotify
