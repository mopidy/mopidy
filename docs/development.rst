***********
Development
***********

Development of Mopidy is coordinated through the IRC channel ``#mopidy`` at
``irc.freenode.net`` and through `GitHub <http://github.com/>`_.


Scope
=====

To limit scope, we will start by implementing an MPD server which only
supports Spotify, and not playback of files from disk. We will make Mopidy
modular, so we can extend it with other backends in the future, like file
playback and other online music services such as Last.fm.


Running tests
=============

To run tests, you need a couple of dependiencies. Some can be installed through Debian/Ubuntu package management::

    sudo aptitude install python-coverage

The rest can be installed using pip::

    sudo aptitude install python-pip python-setuptools bzr
    pip install -r test-requirements.txt

Then, to run all tests::

    python tests


Music Player Daemon (MPD)
=========================

The `MPD protocol documentation <http://www.musicpd.org/doc/protocol/>`_ is a
useful resource. It is rather incomplete with regards to data formats, both for
requests and responses. Thus we have to talk a great deal with the the original
`MPD server <http://mpd.wikia.com/>`_ using telnet to get the details we need
to implement our own MPD server which is compatible with the numerous existing
`MPD clients <http://mpd.wikia.com/wiki/Clients>`_.


spytify
=======

`spytify <http://despotify.svn.sourceforge.net/viewvc/despotify/src/bindings/python/>`_
is the Python bindings for the open source `despotify <http://despotify.se/>`_
library. It got no documentation to speak of, but a couple of examples are
available.

Issues
------

A list of the issues we currently experience with spytify, both bugs and
features we wished was there.

* r483: Sometimes segfaults when traversing stored playlists, their tracks,
  artists, and albums. As it is not predictable, it may be a concurrency issue.

* r499: Segfaults when looking up playlists, both your own lists and other
  peoples shared lists. To reproduce::

    >>> import spytify
    >>> s = spytify.Spytify('alice', 'secret')
    >>> s.lookup('spotify:user:klette:playlist:5rOGYPwwKqbAcVX8bW4k5V')
    Segmentation fault

* r499: Error when accessing an album through an artist. To reproduce::

    >>> import spytify
    >>> s = spytify.Spytify('alice', 'secret')
    >>> result = s.search('Gorillaz')
    >>> artist = result.playlist.tracks[0].artists[0]
    >>> artist
    <Artist: Gorillaz (75f4ed7ec8514e91abaab17306ebbbb6)>
    >>> artist.albums
    ERROR: An unexpected error occurred while tokenizing input
    The following traceback may be corrupted or invalid
    The error message is: ('EOF in multi-line statement', (1423, 0))

    ERROR: An unexpected error occurred while tokenizing input
    The following traceback may be corrupted or invalid
    The error message is: ('EOF in multi-line statement', (1455, 0))

    ---------------------------------------------------------------------------
    TypeError                                 Traceback (most recent call last)

    /home/jodal/<ipython console> in <module>()

    /usr/local/lib/python2.6/dist-packages/spytify.so in spytify.Artist.albums.__get__ (src/spytify.c:4867)()

    /usr/local/lib/python2.6/dist-packages/spytify.so in spytify.Artist.get_full_data (src/spytify.c:4539)()

    TypeError: Cannot convert spytify.AlbumDataFull to spytify.ArtistDataFull


pyspotify
=========

`pyspotify <http://github.com/winjer/pyspotify/>`_ is the Python bindings for
the official Spotify library, libspotify. It got no documentation to speak of,
but multiple examples are available.

Issues
------

A list of the issues we currently experience with pyspotify, both bugs and
features we wished was there.

* None at the moment.
