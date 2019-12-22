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

To get started with Mopidy, begin by reading :ref:`installation`.

.. _getting-help:


**Getting help**

If you get stuck, you can get help at the our `Discourse forum
<https://discourse.mopidy.com/>`_ or in the ``#mopidy-users`` stream on `Zulip
chat <https://mopidy.zulipchat.com/>`_.

If you stumble into a bug or have a feature request, please create an issue in
the `issue tracker <https://github.com/mopidy/mopidy/issues>`_. If you're
unsure if it's a bug or not, ask for help in the forum or the chat first. The
`source code <https://github.com/mopidy/mopidy>`_ may also be of help.

If you want to stay up to date on Mopidy developments, you can follow the
``#mopidy-dev`` stream on `Zulip chat <https://mopidy.zulipchat.com/>`__ or
watch out for announcements on the `Discourse forum
<https://discourse.mopidy.com/>`__.


.. toctree::
    :caption: Usage
    :maxdepth: 2

    installation/index
    running/index
    config
    clients
    troubleshooting


.. toctree::
    :caption: Bundled extensions
    :maxdepth: 1

    ext/file
    ext/m3u
    ext/stream
    ext/http
    ext/softwaremixer


.. toctree::
    :caption: Advanced setups
    :maxdepth: 1

    audiosinks
    icecast
    upnp


.. toctree::
    :caption: About
    :maxdepth: 1

    changelog
    history/index
    versioning
    authors
    sponsors


.. toctree::
    :caption: Development
    :maxdepth: 2

    contributing
    devenv
    extensiondev
    codestyle
    releasing


.. toctree::
    :caption: Reference
    :maxdepth: 2

    api/index
    command
    glossary


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
