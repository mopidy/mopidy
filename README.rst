******
Mopidy
******

`Mopidy`_ is an extensible music server written in Python.

Mopidy plays music from local disk, Spotify, SoundCloud, Google Play Music, and
more. You edit the playlist from any phone, tablet, or computer using a variety
of MPD and web clients.

**Stream music from the cloud**

Vanilla Mopidy only plays music from files and radio streams.  Through
`extensions`_, Mopidy can play music from cloud services like Spotify,
SoundCloud, and Google Play Music.
With Mopidy's extension support, backends for new music sources can be easily
added.

**Mopidy is just a server**

Mopidy is a Python application that runs in a terminal or in the background on
Linux computers or Macs that have network connectivity and audio output.
Out of the box, Mopidy is an HTTP server. If you install the `Mopidy-MPD`_
extension, it becomes an MPD server too. Many additional frontends for
controlling Mopidy are available as extensions.

**Pick your favorite client**

You and the people around you can all connect their favorite MPD or web client
to the Mopidy server to search for music and manage the playlist together.
With a browser or MPD client, which is available for all popular operating
systems, you can control the music from any phone, tablet, or computer.

**Mopidy on Raspberry Pi**

The `Raspberry Pi`_ is an popular device to run Mopidy on, either using
Raspbian, Ubuntu, or Arch Linux.
Pimoroni recommends Mopidy for use with their `Pirate Audio`_ audio gear for
Raspberry Pi.
Mopidy is also a significant building block in the `Pi Musicbox`_ integrated
audio jukebox system for Raspberry Pi.

**Mopidy is hackable**

Mopidy's extension support and Python, JSON-RPC, and JavaScript APIs make
Mopidy a perfect base for your projects.
In one hack, a Raspberry Pi was embedded in an old cassette player. The buttons
and volume control are wired up with GPIO on the Raspberry Pi, and is used to
control playback through a custom Mopidy extension. The cassettes have NFC tags
used to select playlists from Spotify.

.. _Mopidy: https://mopidy.com/
.. _extensions: https://mopidy.com/ext/
.. _Mopidy-MPD: https://mopidy.com/ext/mpd/
.. _Raspberry Pi: https://www.raspberrypi.org/
.. _Pirate Audio: https://shop.pimoroni.com/collections/pirate-audio
.. _Pi Musicbox: https://www.pimusicbox.com/


**Getting started**

To get started with Mopidy, begin by reading the
`installation docs <https://docs.mopidy.com/en/latest/installation/>`_.


**Project resources**

- `Documentation <https://docs.mopidy.com/>`_
- `Discourse forum <https://discourse.mopidy.com/>`_
- `Zulip chat <https://mopidy.zulipchat.com/>`_
- `Source code <https://github.com/mopidy/mopidy>`_
- `Issue tracker <https://github.com/mopidy/mopidy/issues>`_

.. image:: https://img.shields.io/pypi/v/Mopidy.svg?style=flat
    :target: https://pypi.python.org/pypi/Mopidy/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/github/workflow/status/mopidy/mopidy/CI
    :target: https://github.com/mopidy/mopidy/actions
    :alt: CI build status

.. image:: https://img.shields.io/readthedocs/mopidy.svg
    :target: https://docs.mopidy.com/
    :alt: Read the Docs build status

.. image:: https://img.shields.io/codecov/c/github/mopidy/mopidy/develop.svg
    :target: https://codecov.io/gh/mopidy/mopidy
    :alt: Test coverage

.. image:: https://img.shields.io/badge/chat-on%20zulip-brightgreen
    :target: https://mopidy.zulipchat.com/
    :alt: Chat on Zulip
