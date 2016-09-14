******
Mopidy
******

Mopidy is an extensible music server written in Python.

Mopidy plays music from local disk, Spotify, SoundCloud, Google Play Music, and
more. You edit the playlist from any phone, tablet, or computer using a range
of MPD and web clients.

**Stream music from the cloud**

Vanilla Mopidy only plays music from your local disk and radio streams.
Through extensions, Mopidy can play music from cloud services like Spotify,
SoundCloud, and Google Play Music. With Mopidy's extension support, backends
for new music sources can be easily added.

**Mopidy is just a server**

Mopidy is a Python application that runs in a terminal or in the background on
Linux computers or Macs that have network connectivity and audio output. Out of
the box, Mopidy is an MPD and HTTP server. Additional frontends for controlling
Mopidy can be installed from extensions.

**Everybody use their favorite client**

You and the people around you can all connect their favorite MPD or web client
to the Mopidy server to search for music and manage the playlist together. With
a browser or MPD client, which is available for all popular operating systems,
you can control the music from any phone, tablet, or computer.

**Mopidy on Raspberry Pi**

The Raspberry Pi is a popular device to run Mopidy on, either using Raspbian or
Arch Linux. It is quite slow, but it is very affordable. In fact, the
Kickstarter funded Gramofon: Modern Cloud Jukebox project used Mopidy on a
Raspberry Pi to prototype the Gramofon device. Mopidy is also a major building
block in the Pi Musicbox integrated audio jukebox system for Raspberry Pi.

**Mopidy is hackable**

Mopidy's extension support and Python, JSON-RPC, and JavaScript APIs makes
Mopidy perfect for building your own hacks. In one project, a Raspberry Pi was
embedded in an old cassette player. The buttons and volume control are wired up
with GPIO on the Raspberry Pi, and is used to control playback through a custom
Mopidy extension. The cassettes have NFC tags used to select playlists from
Spotify.

To get started with Mopidy, check out
`the installation docs <http://docs.mopidy.com/en/latest/installation/>`_.

- `Documentation <https://docs.mopidy.com/>`_
- `Discussion forum <https://discuss.mopidy.com/>`_
- `Source code <https://github.com/mopidy/mopidy>`_
- `Issue tracker <https://github.com/mopidy/mopidy/issues>`_
- IRC: ``#mopidy`` at `irc.freenode.net <http://freenode.net/>`_
- Announcement list: `mopidy@googlegroups.com <https://groups.google.com/forum/?fromgroups=#!forum/mopidy>`_
- Twitter: `@mopidy <https://twitter.com/mopidy/>`_

.. image:: https://img.shields.io/pypi/v/Mopidy.svg?style=flat
    :target: https://pypi.python.org/pypi/Mopidy/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/travis/mopidy/mopidy/develop.svg?style=flat
    :target: https://travis-ci.org/mopidy/mopidy
    :alt: Travis CI build status

.. image:: https://img.shields.io/coveralls/mopidy/mopidy/develop.svg?style=flat
   :target: https://coveralls.io/r/mopidy/mopidy?branch=develop
   :alt: Test coverage
