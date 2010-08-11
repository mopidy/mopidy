***********************
libspotify installation
***********************

As an alternative to the despotify backend, we are working on a
`libspotify <http://developer.spotify.com/en/libspotify/overview/>`_ backend.
To use the libspotify backend you must install libspotify and
`pyspotify <http://github.com/winjer/pyspotify>`_.

.. warning::

    This backend requires a Spotify premium account, and it requires you to get
    an application key from Spotify before use.


Installing libspotify on Linux
==============================

Download and install libspotify 0.0.4 for your OS and CPU architecture from
https://developer.spotify.com/en/libspotify/.

For 64-bit Linux the process is as follows::

    wget http://developer.spotify.com/download/libspotify/libspotify-0.0.4-linux6-x86_64.tar.gz
    tar zxfv libspotify-0.0.4-linux6-x86_64.tar.gz
    cd libspotify-0.0.4-linux6-x86_64/
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

Check out the pyspotify code, and install it::

    git clone git://github.com/jodal/pyspotify.git
    cd pyspotify/pyspotify/
    sudo python setup.py install
