************
Installation
************

Mopidy itself is a breeze to install, as it just requires a standard Python
installation. The libraries we depend on to connect to the Spotify service is
far more tricky to get working for the time being. Until installation of these
libraries are either well documented by their developers, or the libraries are
packaged for various Linux distributions, we will supply our own installation
guides here.


Dependencies
============

* Python >= 2.6
* pyalsaaudio >= 0.2 (Debian/Ubuntu: python-alsaaudio)
* Dependencies for at least one Mopidy backend:

  * :ref:`despotify`
  * :ref:`libspotify`


.. _despotify:

despotify backend
-----------------

To use the despotify backend, you first need to install despotify and spytify.

.. note::

    This backend requires a Spotify premium account.


Installing despotify
^^^^^^^^^^^^^^^^^^^^

*Linux:* Install despotify's dependencies. At Debian/Ubuntu systems::

    sudo aptitude install libssl-dev zlib1g-dev libvorbis-dev \
        libtool libncursesw5-dev libao-dev

*OS X:* In OS X you need to have `XCode
<http://developer.apple.com/tools/xcode/>`_ and `MacPorts
<http://www.macports.org/>`_ installed. Then, to install despotify's
dependencies::

    sudo port install openssl zlib libvorbis libtool ncursesw libao

*All OS:* Check out revision 503 of the despotify source code::

    svn co https://despotify.svn.sourceforge.net/svnroot/despotify@503

*OS X:* Edit ``despotify/src/Makefile.local.mk`` and uncomment the last two
lines so that it reads::

    ## If you're on Mac OS X and have installed libvorbisfile
    ## via 'port install ..', try uncommenting these lines
    CFLAGS += -I/opt/local/include
    LDFLAGS += -L/opt/local/lib

*All OS:* Build and install despotify::

    cd despotify/src/
    make
    sudo make install


Installing spytify
^^^^^^^^^^^^^^^^^^

spytify's source comes bundled with despotify.

Build and install spytify::

    cd despotify/src/bindings/python/
    export PKG_CONFIG_PATH=../../lib       # Needed on OS X
    make
    sudo make install

To validate that everything is working, run the ``test.py`` script which is
distributed with spytify::

    python test.py

The test script should ask for your username and password (which must be for a
Spotify Premium account), ask for a search query, list all your playlists with
tracks, play 10s from a random song from the search result, pause for two
seconds, play for five more seconds, and quit.


.. _libspotify:

libspotify backend
------------------

As an alternative to the despotify backend, we are working on a libspotify
backend. To use the libspotify backend you must install libspotify and
pyspotify.

.. note::

    This backend requires a Spotify premium account, and it requires you to get
    an application key from Spotify before use.


Installing libspotify
^^^^^^^^^^^^^^^^^^^^^

As libspotify's installation script at the moment is somewhat broken (see this
`GetSatisfaction thread <http://getsatisfaction.com/spotify/topics/libspotify_please_fix_the_installation_script>`_
for details), it is easiest to use the libspotify files bundled with pyspotify.
The files bundled with pyspotify are for 64-bit, so if you run a 32-bit OS, you
must get libspotify from https://developer.spotify.com/en/libspotify/.


Installing pyspotify
^^^^^^^^^^^^^^^^^^^^

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

Test your libspotify setup::

    ./example1.py -u USERNAME -p PASSWORD

.. note::

    Until Spotify fixes their installation script, you'll have to set
    ``LD_LIBRARY_PATH`` every time you are going to use libspotify (in other
    words before starting Mopidy).


Spotify settings
================

Create a file named ``local.py`` in the directory ``mopidy/settings/``. Enter
your Spotify Premium account's username and password into the file, like this::

    SPOTIFY_USERNAME = u'myusername'
    SPOTIFY_PASSWORD = u'mysecret'

Currently the despotify backend is the default. If you want to use the
libspotify backend, copy the Spotify application key to
``mopidy/spotify_appkey.key``, and add the following to
``mopidy/mopidy/settings/local.py``::

    BACKENDS = (u'mopidy.backends.libspotify.LibspotifyBackend',)

For a full list of available settings, see :mod:`mopidy.settings.default`.


Running Mopidy
==============

To start Mopidy, go to the root of the Mopidy project, then simply run::

    python mopidy

To stop Mopidy, press ``CTRL+C``.
