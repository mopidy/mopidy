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

To install Mopidy, start by reading :ref:`installation`.

If you get stuck, we usually hang around at ``#mopidy`` at `irc.freenode.net
<http://freenode.net/>`_ and also got a `mailing list at Google Groups
<https://groups.google.com/forum/?fromgroups=#!forum/mopidy>`_. If you stumble
into a bug or got a feature request, please create an issue in the `issue
tracker <https://github.com/mopidy/mopidy/issues>`_.


Project resources
=================

- `Documentation <http://docs.mopidy.com/>`_
- `Source code <https://github.com/mopidy/mopidy>`_
- `Issue tracker <https://github.com/mopidy/mopidy/issues>`_
- `CI server <https://travis-ci.org/mopidy/mopidy>`_
- IRC: ``#mopidy`` at `irc.freenode.net <http://freenode.net/>`_
- Mailing list: `mopidy@googlegroups.com <https://groups.google.com/forum/?fromgroups=#!forum/mopidy>`_


User documentation
==================

.. toctree::
    :maxdepth: 2

    installation/index
    installation/raspberrypi
    config
    running
    clients/index
    troubleshooting
    authors
    licenses
    changelog


Reference documentation
=======================

.. toctree::
    :maxdepth: 2

    api/index
    modules/index


Development documentation
=========================

.. toctree::
    :maxdepth: 2

    development
    extensiondev


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
