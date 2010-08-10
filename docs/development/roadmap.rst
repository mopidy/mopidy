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
- Read-only support for Spotify through :mod:`mopidy.backends.despotify` and/or
  :mod:`mopidy.backends.libspotify`.
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


Stuff we really want to do, but just not right now
==================================================

- Replace libspotify with `openspotify
  <http://github.com/noahwilliamsson/openspotify>`_ for
  :mod:`mopidy.backends.libspotify`. *Update:* Seems like openspotify
  development has stalled.
- Create `Debian packages <http://www.debian.org/doc/maint-guide/>`_ of all our
  dependencies and Mopidy itself (hosted in our own Debian repo until we get
  stuff into the various distros) to make Debian/Ubuntu installation a breeze.
- **[WIP]** Create `Homebrew <http://mxcl.github.com/homebrew/>`_ recipies for
  all our dependencies and Mopidy itself to make OS X installation a breeze.
- Run frontend tests against a real MPD server to ensure we are in sync.
- Start working with MPD client maintainers to get rid of weird assumptions
  like only searching for first two letters and doing the rest of the filtering
  locally in the client, etc.


Crazy stuff we had to write down somewhere
==========================================

- Add an `XMMS2 <http://www.xmms2.org/>`_ frontend, so Mopidy can serve XMMS2
  clients.
- Add support for serving the music as an `Icecast <http://www.icecast.org/>`_
  stream instead of playing it locally.
- Integrate with `Squeezebox <http://www.logitechsqueezebox.com/>`_ in some
  way.
- AirPort Express support, like in
  `PulseAudio <http://git.0pointer.de/?p=pulseaudio.git;a=blob;f=src/modules/raop/raop_client.c;hb=HEAD>`_.
- DNLA and/or UPnP support. Maybe using
  `Coherence <http://coherence-project.org/>`_.
- `Media Player Remote Interfacing Specification
  <http://en.wikipedia.org/wiki/Media_Player_Remote_Interfacing_Specification>`_
  support.
