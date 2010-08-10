**********************
Despotify installation
**********************

To use the `Despotify <http://despotify.se/>`_ backend, you first need to
install Despotify and spytify.

.. warning::

    This backend requires a Spotify premium account.


Installing Despotify on Linux
=============================

Install Despotify's dependencies. At Debian/Ubuntu systems::

    sudo aptitude install libssl-dev zlib1g-dev libvorbis-dev \
        libtool libncursesw5-dev libao-dev python-dev

Check out revision 508 of the Despotify source code::

    svn checkout https://despotify.svn.sourceforge.net/svnroot/despotify@508

Build and install Despotify::

    cd despotify/src/
    sudo make install

When Despotify has been installed, continue with :ref:`spytify_installation`.


Installing Despotify on OS X
============================

In OS X you need to have `XCode <http://developer.apple.com/tools/xcode/>`_ and
`Homebrew <http://mxcl.github.com/homebrew/>`_ installed. Then, to install
Despotify::

    brew install despotify

When Despotify has been installed, continue with :ref:`spytify_installation`.


.. _spytify_installation:

Installing spytify
==================

spytify's source comes bundled with despotify. If you haven't already checkout
out the despotify source, do it now::

    svn checkout https://despotify.svn.sourceforge.net/svnroot/despotify@508

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
