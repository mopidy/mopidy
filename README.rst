******
mopidy
******

mopidy is an MPD server with a Spotify backend.


Goal
====

Using a standard MPD client we want to search for music in Spotify, manage
Spotify play lists and play music from Spotify.

To limit scope, we will start by implementing an MPD server which only
supports Spotify, and not playback of files from disk. We will make mopidy
modular, so we can extend it with other backends in the future, like file
playback and other online music services such as Last.fm.


Backends
========

To use the despotify backend, you first need to install despotify and spytify.
Alternatively, we are working on a libspotify backend, which requires you to
install libspotify and pyspotify.

Both backends require a Spotify premium account, while only the libspotify
backend requires you to get an application key from Spotify before use.


Installing despotify and spytify
--------------------------------

Check out the despotify source code revision 483 (or possibly newer)::

    svn co https://despotify.svn.sourceforge.net/svnroot/despotify@483 despotify

Install despotify's dependencies. At Debian/Ubuntu systems::

    sudo aptitude install libssl-dev zlib1g-dev libvorbis-dev \
        libtool libncursesw5-dev libao-dev

Build and install despotify::

    cd despotify/src/
    make
    sudo make install

Build and install spytify::

    cd despotify/src/bindings/python/
    make
    sudo make install

To validate that everything is working, run the ``test.py`` script which is
distributed with spytify::

    python test.py

The test script should ask for your username and password (which must be for a
Spotify Premium account), ask for a search query, list all your playlists with
tracks, play 10s from a random song from the search result, pause for two
seconds, play for five more seconds, and quit.


Installing libspotify and pyspotify
-----------------------------------

As libspotify's installation script at the moment is somewhat broken (see this
`GetSatisfaction thread <http://getsatisfaction.com/spotify/topics/libspotify_please_fix_the_installation_script>`_
for details), it is easiest to use the libspotify files bundled with pyspotify.
The files bundled with pyspotify are for 64-bit, so if you run a 32-bit OS, you
must get libspotify from https://developer.spotify.com/en/libspotify/.

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

Until Spotify fixes their installation script, you'll have to set
``LD_LIBRARY_PATH`` every time you are going to use libspotify (in other words
before starting mopidy).


Running mopidy
==============

Create a file name ``local_settings.py`` in the same directory as
``settings.py``. Enter your Spotify Premium account's username and password
into the file, like this::

    SPOTIFY_USERNAME = u'myusername'
    SPOTIFY_PASSWORD = u'mysecret'

To start mopidy, go to the root of the mopidy project, then simply run::

    python mopidy

To stop mopidy, press ``CTRL+C``.


Running tests
=============

To run tests, you need a couple of dependiencies. Some can be installed through Debian/Ubuntu package management::

    sudo aptitude install python-coverage

The rest can be installed using pip::

    sudo aptitude install python-pip python-setuptools bzr
    pip install -r test-requirements.txt

Then, to run all tests::

    python tests


Resources
=========

- MPD

  - `MPD protocol documentation <http://www.musicpd.org/doc/protocol/>`_
  - The original `MPD server <http://mpd.wikia.com/>`_

- Spotify

  - `spytify <http://despotify.svn.sourceforge.net/viewvc/despotify/src/bindings/python/>`_,
    the Python bindings for `despotify <http://despotify.se/>`_
  - `pyspotify <http://github.com/winjer/pyspotify/>`_,
    Python bindings for the official Spotify library, libspotify
  - `Spotify's official metadata API <http://developer.spotify.com/en/metadata-api/overview/>`_
