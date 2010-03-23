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


Installing libspotify
=====================

As libspotify's installation script at the moment is somewhat broken (see this
`GetSatisfaction thread <http://getsatisfaction.com/spotify/topics/libspotify_please_fix_the_installation_script>`_
for details), it is easiest to use the libspotify files bundled with pyspotify.
The files bundled with pyspotify are for 64-bit, so if you run a 32-bit OS, you
must get libspotify from https://developer.spotify.com/en/libspotify/.


Installing pyspotify
====================

Install pyspotify's dependencies. At Debian/Ubuntu systems::

    sudo aptitude install python-alsaaudio

Check out the pyspotify code, and install it::

    git clone git://github.com/winjer/pyspotify.git
    cd pyspotify
    export LD_LIBRARY_PATH=$PWD/lib
    sudo python setup.py develop

Apply for an application key at
https://developer.spotify.com/en/libspotify/application-key, download the
binary version, and place the file at ``pyspotify/spotify_appkey.key``.


Testing the installation
========================

Test your libspotify setup::

    examples/example1.py -u USERNAME -p PASSWORD

.. note::

    Until Spotify fixes their installation script, you'll have to set
    ``LD_LIBRARY_PATH`` every time you are going to use libspotify (in other
    words before starting Mopidy).


Setting up Mopidy to use libspotify
===================================

Currently :mod:`mopidy.backends.despotify` is the default
backend. If you want to use :mod:`mopidy.backends.libspotify`
instead, copy the Spotify application key to ``~/.mopidy/spotify_appkey.key``,
and add the following to ``~/.mopidy/settings.py``::

    BACKENDS = (u'mopidy.backends.libspotify.LibspotifyBackend',)
