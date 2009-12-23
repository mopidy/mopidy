mopidy
======

mopidy is a MPD server with a Spotify backend.


Goal
----

Using a standard MPD client we want to search for music in Spotify, manage
Spotify play lists and play music from Spotify.

To limit scope, we will start by implementing a MPD server which only supports
Spotify, and not playback of files from disk. We will make mopidy modular, so
we can extend it with other backends in the future, like file playback and
other online music services such as Last.fm.


Architecture
------------

**TODO**


Resources
---------

- MPD

  - `MPD protocol documentation <http://www.musicpd.org/doc/protocol/>`_
  - The original `MPD server <http://mpd.wikia.com/>`_

- Spotify

  - `spytify <http://despotify.svn.sourceforge.net/viewvc/despotify/src/bindings/python/>`_,
    the Python bindings for `despotify <http://despotify.se/>`_
  - `Spotify's official metadata API <http://developer.spotify.com/en/metadata-api/overview/>`_
  - `pyspotify <http://code.google.com/p/pyspotify/>`_,
    Python bindings for the official Spotify library, libspotify
