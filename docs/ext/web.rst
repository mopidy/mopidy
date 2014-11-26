.. _ext-web:

**************
Web extensions
**************

Here you can find a list of external packages that extend Mopidy with
additional web interfaces by implementing the :ref:`http-server-api`, which
was added in Mopidy 0.19, and optionally using the :ref:`http-api`.

This list is moderated and updated on a regular basis. If you want your package
to show up here, follow the :ref:`guide on creating extensions <extensiondev>`.


.. _http-explore-extension:

Mopidy-API-Explorer
===================

https://github.com/dz0ny/mopidy-api-explorer

Web extension for browsing the Mopidy HTTP API.

.. image:: /ext/api_explorer.png
    :width: 1176
    :height: 713

To install, run::

    pip install Mopidy-API-Explorer


Mopidy-HTTP-Kuechenradio
=========================

https://github.com/tkem/mopidy-http-kuechenradio

A deliberately simple Mopidy Web client for mobile devices. Made with jQuery
Mobile by Thomas Kemmer.

To install, run::

    pip install Mopidy-HTTP-Kuechenradio


Mopidy-Moped
============

https://github.com/martijnboland/moped

A Mopidy web client made with AngularJS by Martijn Boland.

.. image:: /ext/moped.png
    :width: 720
    :height: 450

To install, run::

    pip install Mopidy-Moped


Mopidy-MusicBox-Webclient
=========================

https://github.com/woutervanwijk/Mopidy-MusicBox-Webclient

The first web client for Mopidy, made with jQuery Mobile by Wouter van Wijk.
Also the web client used for Wouter's popular `Pi Musicbox
<http://www.pimusicbox.com/>`_ image for Raspberry Pi.

.. image:: /ext/musicbox_webclient.png
    :width: 1275
    :height: 600

To install, run::

    pip install Mopidy-MusicBox-Webclient


Other web clients
=================

There's also some other web clients for Mopidy that use the :ref:`http-api`,
but isn't installable using ``pip``:

- `Apollo Player <https://github.com/samcreate/Apollo-Player>`_
- `JukePi <https://github.com/meantimeit/jukepi>`_

In addition, there's several web based MPD clients, which doesn't use the
:ref:`ext-http` frontend at all, but connect to Mopidy through our
:ref:`ext-mpd` frontend. For a list of those, see :ref:`mpd-web-clients`.
