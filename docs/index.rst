******
Mopidy
******

Mopidy is a music server which can play music both from multiple sources, like
your :ref:`local hard drive <ext-local>`, :ref:`radio streams <ext-stream>`,
and from Spotify and SoundCloud. Searches combines results from all music
sources, and you can mix tracks from all sources in your play queue. Your
playlists from Spotify or SoundCloud are also available for use.

To control your Mopidy music server, you can use one of Mopidy's :ref:`web
clients <http-clients>`, the :ref:`Ubuntu Sound Menu <ubuntu-sound-menu>`, any
device on the same network which can control :ref:`UPnP MediaRenderers
<upnp-clients>`, or any :ref:`MPD client <mpd-clients>`. MPD clients are
available for many platforms, including Windows, OS X, Linux, Android and iOS.

To get started with Mopidy, start by reading :ref:`installation`.

If you get stuck, we usually hang around at ``#mopidy`` at `irc.freenode.net
<http://freenode.net/>`_ and also have a `mailing list at Google Groups
<https://groups.google.com/forum/?fromgroups=#!forum/mopidy>`_. If you stumble
into a bug or got a feature request, please create an issue in the `issue
tracker <https://github.com/mopidy/mopidy/issues>`_. The `source code
<https://github.com/mopidy/mopidy>`_ may also be of help. If you want to stay
up to date on Mopidy developments, you can follow `@mopidy
<https://twitter.com/mopidy/>`_ on Twitter.


Usage
=====

.. toctree::
    :maxdepth: 2

    installation/index
    installation/raspberrypi
    config
    running
    troubleshooting


.. _ext:

Extensions
==========

.. toctree::
    :maxdepth: 2

    ext/local
    ext/stream
    ext/http
    ext/mpd
    ext/external


Clients
=======

.. toctree::
    :maxdepth: 2

    clients/http
    clients/mpd
    clients/mpris
    clients/upnp


About
=====

.. toctree::
    :maxdepth: 1

    authors
    changelog
    versioning


Development
===========

.. toctree::
    :maxdepth: 1

    contributing
    devtools
    codestyle
    extensiondev


Reference
=========

.. toctree::
    :maxdepth: 2

    glossary
    commands/index
    api/index
    modules/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
