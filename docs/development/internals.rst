*********
Internals
*********

Some of the following notes and details will hopefully be useful when you start
developing on Mopidy, while some may only be useful when you get deeper into
specific parts of Mopidy.

In addition to what you'll find here, don't forget the :doc:`/api/index`.


Class instantiation and usage
=============================

The following diagram shows how Mopidy with the despotify backend and ALSA
mixer is wired together. The gray nodes are part of external dependencies, and
not Mopidy.

.. digraph:: class_instantiation_and_usage

    "spytify" [ color="gray" ]
    "despotify" [ color="gray" ]
    "alsaaudio" [ color="gray" ]
    "__main__" -> "MpdServer" [ label="create 1" ]
    "__main__" -> "AlsaMixer" [ label="create 1" ]
    "__main__" -> "DespotifyBackend" [ label="create 1" ]
    "MpdServer" -> "MpdSession" [ label="create 1 per client" ]
    "MpdSession" -> "MpdHandler" [ label="pass MPD requests to" ]
    "MpdHandler" -> "DespotifyBackend" [ label="use backend API" ]
    "DespotifyBackend" -> "spytify" [ label="use Python wrapper" ]
    "spytify" -> "despotify" [ label="use C library" ]
    "DespotifyBackend" -> "AlsaMixer" [ label="use mixer API" ]
    "AlsaMixer" -> "alsaaudio" [ label="use Python library" ]


Notes on despotify/spytify
==========================

`spytify <http://despotify.svn.sourceforge.net/viewvc/despotify/src/bindings/python/>`_
is the Python bindings for the open source `despotify <http://despotify.se/>`_
library. It got no documentation to speak of, but a couple of examples are
available.

A list of the issues we currently experience with spytify, both bugs and
features we wished was there:

- r503: Sometimes segfaults when traversing stored playlists, their tracks,
  artists, and albums. As it is not predictable, it may be a concurrency issue.

- r503: Segfaults when looking up playlists, both your own lists and other
  peoples shared lists. To reproduce::

    >>> import spytify
    >>> s = spytify.Spytify('alice', 'secret')
    >>> s.lookup('spotify:user:klette:playlist:5rOGYPwwKqbAcVX8bW4k5V')
    Segmentation fault


Notes on libspotify/pyspotify
============================================

`pyspotify <http://github.com/winjer/pyspotify/>`_ is the Python bindings for
the official Spotify library, libspotify. It got no documentation to speak of,
but multiple examples are available. Like libspotify, pyspotify's calls are
mostly asynchronous.

A list of the issues we currently experience with pyspotify, both bugs and
features we wished was there:

- None at the moment.
