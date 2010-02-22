***********
Development
***********

Development of Mopidy is coordinated through the IRC channel ``#mopidy`` at
``irc.freenode.net`` and through `GitHub <http://github.com/>`_.


API documentation
=================

.. toctree::
    :glob:

    api/**

Scope
=====

To limit scope, we will start by implementing an MPD server which only
supports Spotify, and not playback of files from disk. We will make Mopidy
modular, so we can extend it with other backends in the future, like file
playback and other online music services such as Last.fm.


Code style
==========

We generally follow the `PEP-8 <http://www.python.org/dev/peps/pep-0008/>`_
style guidelines, with a couple of notable exceptions:

- We indent continuation lines with four spaces more than the previous line.
  For example::

    from mopidy.backends import (BaseBackend, BaseCurrentPlaylistController,
        BasePlaybackController, BaseLibraryController,
        BaseStoredPlaylistsController)

  And not::

    from mopidy.backends import (BaseBackend, BaseCurrentPlaylistController,
                                 BasePlaybackController, BaseLibraryController,
                                 BaseStoredPlaylistsController)

- An exception to the previous exception: When continuing control flow
  statements like ``if``, ``for`` and ``while``, we indent with eight spaces
  more than the previous line. In other words, the line is indented one level
  further to the right than the following block of code. For example::

    if (old_state in (self.PLAYING, self.STOPPED)
            and new_state == self.PLAYING):
        self._play_time_start()

  And not::

    if (old_state in (self.PLAYING, self.STOPPED)
        and new_state == self.PLAYING):
        self._play_time_start()


Running tests
=============

To run tests, you need a couple of dependencies. Some can be installed through
Debian/Ubuntu package management::

    sudo aptitude install python-coverage

The rest (or all dependencies if you want to) can be installed using pip::

    sudo aptitude install python-pip python-setuptools bzr
    sudo pip install -r requirements-tests.txt

Then, to run all tests::

    python tests


Generating documentation
========================

To generate documentation, you also need some additional dependencies. You can either install them through Debian/Ubuntu package management::

    sudo aptitude install python-sphinx

Or, install them using pip::

    sudo aptitude install python-pip python-setuptools
    sudo pip install -r requirements-docs.txt

Then, to generate docs::

    cd docs/
    make        # For help on available targets
    make html   # To generate HTML docs


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

* r503: Segfaults when looking up playlists, both your own lists and other
  peoples shared lists. To reproduce::

    >>> import spytify
    >>> s = spytify.Spytify('alice', 'secret')
    >>> s.lookup('spotify:user:klette:playlist:5rOGYPwwKqbAcVX8bW4k5V')
    Segmentation fault


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
