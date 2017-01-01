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


Mopidy-Local-Images
===================

https://github.com/tkem/mopidy-local-images

Not a full-featured web client, but rather a local library and web
extension which allows other web clients access to album art embedded
in local media files.

.. image:: /ext/local_images.jpg
    :width: 640
    :height: 480

To install, run::

    pip install Mopidy-Local-Images


Mopidy-Material-Webclient
=========================

https://github.com/matgallacher/mopidy-material-webclient

A Mopidy web client with an Android Material design feel.

.. image:: /ext/material_webclient.png
   :width: 960
   :height: 520

To install, run::

    pip install Mopidy-Material-Webclient


Mopidy-Mobile
=============

https://github.com/tkem/mopidy-mobile

A Mopidy web client extension and hybrid mobile app, made with Ionic,
AngularJS and Apache Cordova by Thomas Kemmer.

.. image:: /ext/mobile.png
    :width: 1024
    :height: 606

To install, run::

    pip install Mopidy-Mobile


Mopidy-Moped
============

https://github.com/martijnboland/moped

A Mopidy web client made with AngularJS by Martijn Boland.

.. image:: /ext/moped.png
    :width: 720
    :height: 450

To install, run::

    pip install Mopidy-Moped


Mopidy-Mopify
=============

https://github.com/dirkgroenen/mopidy-mopify

A web client that uses external web services to provide additional features and
a more "complete" Spotify music experience. It's currently targeted at people
using Spotify through Mopidy. Made by Dirk Groenen.

.. image:: /ext/mopify.jpg
    :width: 800
    :height: 416

To install, run::

    pip install Mopidy-Mopify


Mopidy-MusicBox-Webclient
=========================

https://github.com/pimusicbox/mopidy-musicbox-webclient

The first web client for Mopidy, made with jQuery Mobile by Wouter van Wijk.
Also the web client used for Wouter's popular `Pi Musicbox
<http://www.pimusicbox.com/>`_ image for Raspberry Pi.

.. image:: /ext/musicbox_webclient.png
    :width: 1275
    :height: 600

To install, run::

    pip install Mopidy-MusicBox-Webclient


Mopidy-Party
============

https://github.com/Lesterpig/mopidy-party

Minimal web client designed for collaborative music management during parties.

.. image:: /ext/mopidy_party.png

To install, run::

    pip install Mopidy-Party


Mopidy-Simple-Webclient
=======================

https://github.com/xolox/mopidy-simple-webclient

A minimalistic web client targeted for mobile devices. Made with jQuery and
Bootstrap by Peter Odding.

.. image:: /ext/simple_webclient.png
    :width: 473
    :height: 373

To install, run::

    pip install Mopidy-Simple-Webclient


Mopidy-Spotmop
==============

https://github.com/jaedb/spotmop

A client targeted at Spotify users. Made by James Barnsley.

.. image:: /ext/spotmop.jpg
    :width: 720
    :height: 455

To install, run::

    pip install Mopidy-Spotmop


Mopidy-WebSettings
==================

https://github.com/pimusicbox/mopidy-websettings

A web extension for changing settings. Used by the Pi MusicBox distribution
for Raspberry Pi, but also usable for other projects.


Mopster
=======

https://github.com/cowbell/mopster

Simple web client hosted online written in Ember.js and styled using basic
Bootstrap by Wojciech Wnętrzak.

.. image:: /ext/mopster.png
    :width: 1275
    :height: 628

To use, just visit http://mopster.cowbell-labs.com/.


Mopidy-Jukepi
=============

https://github.com/meantimeit/jukepi

A Mopidy web client built with Backbone by connrs.

.. image:: /ext/mopidy_jukepi.png
    :width: 1260
    :height: 961

To install, run::

    pip install Mopidy-Jukepi

Other web clients
=================

There are also some other web clients for Mopidy that use the :ref:`http-api`
but are not installable using ``pip``:

- `Apollo Player <https://github.com/samcreate/Apollo-Player>`_

In addition, there are several web based MPD clients, which doesn't use the
:ref:`ext-http` frontend at all, but connect to Mopidy through our
:ref:`ext-mpd` frontend. For a list of those, see :ref:`mpd-web-clients`.
