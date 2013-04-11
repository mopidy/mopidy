******
Mopidy
******

Mopidy is a music server which can play music both from your :ref:`local hard
drive <local-backend>` and from :ref:`Spotify <spotify-backend>`. Searches
returns results from both your local hard drive and from Spotify, and you can
mix tracks from both sources in your play queue. Your Spotify playlists are
also available for use, though we don't support modifying them yet.

To control your music server, you can use the :ref:`Ubuntu Sound Menu
<ubuntu-sound-menu>` on the machine running Mopidy, any device on the same
network which can control UPnP MediaRenderers (see :ref:`upnp-clients`), or any
:ref:`MPD client <mpd-clients>`. MPD clients are available for most platforms,
including Windows, Mac OS X, Linux, Android, and iOS.

To get started with Mopidy, start by reading :ref:`installation`.

If you get stuck, we usually hang around at ``#mopidy`` at `irc.freenode.net
<http://freenode.net/>`_ and also got a `mailing list at Google Groups
<https://groups.google.com/forum/?fromgroups=#!forum/mopidy>`_. If you stumble
into a bug or got a feature request, please create an issue in the `issue
tracker <https://github.com/mopidy/mopidy/issues>`_. The `source code
<https://github.com/mopidy/mopidy>`_ may also be of help.


Introduction
============

.. toctree::
    :maxdepth: 2

    installation/index
    installation/raspberrypi
    config
    running
    clients/index
    troubleshooting


Extensions
==========

TODO


About
=====

.. toctree::
    :maxdepth: 1

    authors
    licenses
    changelog


Development
===========

.. toctree::
    :maxdepth: 2

    contributing
    development
    extensiondev
    api/index
    modules/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
