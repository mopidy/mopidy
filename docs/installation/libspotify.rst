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

.. note::

    This product uses SPOTIFY CORE but is not endorsed, certified or otherwise
    approved in any way by Spotify. Spotify is the registered trade mark of the
    Spotify Group.


Installing libspotify
=====================


On Linux from APT archive
-------------------------

If you run a Debian based Linux distribution, like Ubuntu, see
http://apt.mopidy.com/ for how to the Mopidy APT archive as a software source
on your installation. Then, simply run::

    sudo apt-get install libspotify8

When libspotify has been installed, continue with
:ref:`pyspotify_installation`.


On Linux from source
--------------------

Download and install libspotify 0.0.8 for your OS and CPU architecture from
https://developer.spotify.com/en/libspotify/.

For 64-bit Linux the process is as follows::

    wget http://developer.spotify.com/download/libspotify/libspotify-0.0.8-linux6-x86_64.tar.gz
    tar zxfv libspotify-0.0.8-linux6-x86_64.tar.gz
    cd libspotify-0.0.8-linux6-x86_64/
    sudo make install prefix=/usr/local
    sudo ldconfig

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
    brew install `brew outdated`

When libspotify has been installed, continue with
:ref:`pyspotify_installation`.


.. _pyspotify_installation:

Installing pyspotify
====================

When you've installed libspotify, it's time for making it available from Python
by installing pyspotify.


On Linux from APT archive
-------------------------

Assuming that you've already set up http://apt.mopidy.com/ as a software
source, run::

    sudo apt-get install python-spotify

If you haven't already installed libspotify, this command will install both
libspotify and pyspotify for you.


On Linux/OS X from source
-------------------------

On Linux, you need to get the Python development files installed. On
Debian/Ubuntu systems run::

    sudo apt-get install python-dev

On OS X no additional dependencies are needed.

Then get, build, and install the latest releast of pyspotify using ``pip``::

    sudo pip install -U pyspotify

Or using the older ``easy_install``::

    sudo easy_install pyspotify
