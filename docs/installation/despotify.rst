**********************
despotify installation
**********************

To use the `despotify <http://despotify.se/>`_ backend, you first need to
install despotify and spytify.

.. warning::

    This backend requires a Spotify premium account.


Installing despotify
====================

*Linux:* Install despotify's dependencies. At Debian/Ubuntu systems::

    sudo aptitude install libssl-dev zlib1g-dev libvorbis-dev \
        libtool libncursesw5-dev libao-dev python-dev

*OS X:* In OS X you need to have `XCode
<http://developer.apple.com/tools/xcode/>`_ installed, and either `MacPorts
<http://www.macports.org/>`_ or `Homebrew <http://mxcl.github.com/homebrew/>`_.

*OS X, Homebrew:* Install dependencies::

    brew install libvorbis ncursesw libao pkg-config

*OS X, MacPorts:* Install dependencies::

    sudo port install libvorbis libtool ncursesw libao

*All OS:* Check out revision 508 of the despotify source code::

    svn checkout https://despotify.svn.sourceforge.net/svnroot/despotify@508

*OS X, MacPorts:* Copy ``despotify/src/Makefile.local.mk.dist`` to
``despotify/src/Makefile.local.mk`` and uncomment the last two lines of the new
file so that it reads::

    ## If you're on Mac OS X and have installed libvorbisfile
    ## via 'port install ..', try uncommenting these lines
    CFLAGS += -I/opt/local/include
    LDFLAGS += -L/opt/local/lib

*All OS:* Build and install despotify::

    cd despotify/src/
    sudo make install


Installing spytify
==================

spytify's source comes bundled with despotify.

Build and install spytify::

    cd despotify/src/bindings/python/
    export PKG_CONFIG_PATH=../../lib       # Needed on OS X
    sudo make install


Testing the installation
========================

To validate that everything is working, run the ``test.py`` script which is
distributed with spytify::

    python test.py

The test script should ask for your username and password (which must be for a
Spotify Premium account), ask for a search query, list all your playlists with
tracks, play 10s from a random song from the search result, pause for two
seconds, play for five more seconds, and quit.
