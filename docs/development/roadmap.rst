*******
Roadmap
*******

This is the current roadmap and collection of wild ideas for future Mopidy
development. This is intended to be a living document and may change at any
time.

Version 0.1
===========

- Core MPD server functionality working. Gracefully handle clients' use of
  non-supported functionality.
- Read-only support for Spotify through :mod:`mopidy.backends.libspotify`.
- Initial support for local file playback through
  :mod:`mopidy.backends.local`. The state of local file playback will not
  block the release of 0.1.


Version 0.2 and 0.3
===================

0.2 will be released when we reach one of the following two goals. 0.3 will be
released when we reach the other goal.

- Write-support for Spotify. I.e. playlist management.
- Support for using multiple Mopidy backends simultaneously. Should make it
  possible to have both Spotify tracks and local tracks in the same playlist.


Stuff we want to do, but not right now, and maybe never
=======================================================

- Packaging and distribution:

  - **[PENDING]** Create `Homebrew <http://mxcl.github.com/homebrew/>`_
    recipies for all our dependencies and Mopidy itself to make OS X
    installation a breeze. See `Homebrew's issue #1612
    <http://github.com/mxcl/homebrew/issues/issue/1612>`_.
  - Create `Debian packages <http://www.debian.org/doc/maint-guide/>`_ of all
    our dependencies and Mopidy itself (hosted in our own Debian repo until we
    get stuff into the various distros) to make Debian/Ubuntu installation a
    breeze.

- Compatability:

  - Run frontend tests against a real MPD server to ensure we are in sync.
  - Start working with MPD client maintainers to get rid of weird assumptions
    like only searching for first two letters and doing the rest of the
    filtering locally in the client (:issue:`1`), etc.

- Backends:

  - `Last.fm <http://www.last.fm/api>`_
  - `WIMP <http://twitter.com/wimp/status/8975885632>`_
  - DNLA/UPnP to Mopidy can play music from other DNLA MediaServers.

- Frontends:

  - Publish the server's presence to the network using `Zeroconf
    <http://en.wikipedia.org/wiki/Zeroconf>`_/Avahi.
  - D-Bus/`MPRIS <http://www.mpris.org/>`_
  - REST/JSON web service with a jQuery client as example application. Maybe
    based upon `Tornado <http://github.com/facebook/tornado>`_ and `jQuery
    Mobile <http://jquerymobile.com/>`_.
  - DNLA/UPnP to Mopidy can be controlled from i.e. TVs.
  - `XMMS2 <http://www.xmms2.org/>`_
  - LIRC frontend for controlling Mopidy with a remote.

- Mixers:

  - LIRC mixer for controlling arbitrary amplifiers remotely.

- Audio streaming:

  - Ogg Vorbis/MP3 audio stream over HTTP, to MPD clients, `Squeezeboxes
    <http://www.logitechsqueezebox.com/>`_, etc.
  - Feed audio to an `Icecast <http://www.icecast.org/>`_ server.
  - Stream to AirPort Express using `RAOP
    <http://en.wikipedia.org/wiki/Remote_Audio_Output_Protocol>`_.
