*******
Roadmap
*******

This is the current roadmap and collection of wild ideas for future Mopidy
development.


Scope for the first release
===========================

This was was the plan written down when we started developing Mopidy, and we
still keep quite close to it:

    To limit scope, we will start by implementing an MPD server which only
    supports Spotify, and not playback of files from disk. We will make Mopidy
    modular, so we can extend it with other backends in the future, like file
    playback and other online music services such as Last.fm.


Stuff we really want to do, but just not right now
==================================================

- Replace libspotify with `openspotify
  <http://github.com/noahwilliamsson/openspotify>`_ for the
  ``LibspotifyBackend``.
- A backend for playback from local disk. Quite a bit of work on a `gstreamer
  <http://gstreamer.freedesktop.org/>`_ backend has already been done by Thomas
  Adamcik.
- Support multiple backends at the same time. It would be really nice to have
  tracks from local disk and Spotify tracks in the same playlist.
- **[Done]** Package Mopidy as a `Python package
  <http://guide.python-distribute.org/>`_.
- Get a build server, i.e. `Hudson <http://hudson-ci.org/>`_, up and running
  which runs our test suite on all relevant platforms (Ubuntu, OS X, etc.) and
  creates nightly packages (see next items).
- Create `Debian packages <http://www.debian.org/doc/maint-guide/>`_ of all our
  dependencies and Mopidy itself (hosted in our own Debian repo until we get
  stuff into the various distros) to make Debian/Ubuntu installation a breeze.
- Create `Homebrew <http://mxcl.github.com/homebrew/>`_ recipies for all our
  dependencies and Mopidy itself to make OS X installation a breeze.


Crazy stuff we had to write down somewhere
==========================================

- Add or create a new frontend protocol other than MPD. The MPD protocol got
  quite a bit of legacy and it is badly documented. The amount of available
  client implementations is MPD's big win.
- Add support for storing (Spotify) music to disk.
- Add support for serving the music as an `Icecast <http://www.icecast.org/>`_
  stream instead of playing it locally.
- Integrate with `Squeezebox <http://www.logitechsqueezebox.com/>`_ in some
  way.
- AirPort Express support, like in
  `PulseAudio <http://git.0pointer.de/?p=pulseaudio.git;a=blob;f=src/modules/raop/raop_client.c;hb=HEAD>`_.
- **[Done]** NAD/Denon amplifier mixer through their RS-232 connection.
- DNLA and/or UPnP support.
