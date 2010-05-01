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

**TODO** Test and document installation on OS X.


Installing libspotify
=====================

Download and install libspotify 0.0.4 for your OS and CPU architecture from
https://developer.spotify.com/en/libspotify/.

For 64-bit Linux the process is as follows::

    wget http://developer.spotify.com/download/libspotify/libspotify-0.0.4-linux6-x86_64.tar.gz
    tar zxfv libspotify-0.0.4-linux6-x86_64.tar.gz
    cd libspotify-0.0.4-linux6-x86_64/
    sudo make install prefix=/usr/local
    sudo ldconfig


Installing pyspotify
====================

Install pyspotify's dependencies. At Debian/Ubuntu systems::

    sudo aptitude install python-alsaaudio

Check out the pyspotify code, and install it::

    git clone git://github.com/jodal/pyspotify.git
    cd pyspotify
    sudo python setup.py develop

Apply for an application key at
https://developer.spotify.com/en/libspotify/application-key, download the
binary version, and place the file at ``pyspotify/spotify_appkey.key``.


Testing the installation
========================

Test your libspotify setup::

    examples/example1.py -u USERNAME -p PASSWORD


Setting up Mopidy to use libspotify
===================================

Currently :mod:`mopidy.backends.despotify` is the default
backend. If you want to use :mod:`mopidy.backends.libspotify`
instead, copy the Spotify application key to ``~/.mopidy/spotify_appkey.key``,
and add the following to ``~/.mopidy/settings.py``::

    BACKENDS = (u'mopidy.backends.libspotify.LibspotifyBackend',)
