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

.. image:: /ext/api_explorer.jpg
    :width: 696
    :height: 422

To install, run::

    pip install Mopidy-API-Explorer


Mopidy-Auto
===========

https://github.com/gotling/mopidy-auto

Mopidy extension to automate music playback based on time of day.

.. warning::
    This extension reacts to the events ``tracklist_changed``,
    ``track_playback_ended``, and ``track_playback_resumed`` to accomplish its
    goals. Other web extensions will not work as expected when this extension
    is installed.

.. image:: /ext/auto.jpg
    :width: 533
    :height: 370

To install, run::

    pip install Mopidy-Auto


Mopidy-Iris
===========

https://github.com/jaedb/iris

A comprehensive and mobile-friendly client that presents your library and
extensions in a user-friendly and intuitive interface. Built using React and
Redux. Made by James Barnsley.

.. image:: /ext/iris.jpg
    :width: 696
    :height: 506

To install, run::

    pip install Mopidy-Iris


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

.. image:: /ext/material_webclient.jpg
   :width: 696
   :height: 377

To install, run::

    pip install Mopidy-Material-Webclient


Mopidy-Mobile
=============

https://github.com/tkem/mopidy-mobile

A Mopidy web client extension and hybrid mobile app, made with Ionic,
AngularJS and Apache Cordova by Thomas Kemmer.

.. image:: /ext/mobile.jpg
    :width: 696
    :height: 412

To install, run::

    pip install Mopidy-Mobile


Mopidy-Moped
============

https://github.com/martijnboland/moped

A Mopidy web client made with AngularJS by Martijn Boland.

.. image:: /ext/moped.jpg
    :width: 696
    :height: 435

To install, run::

    pip install Mopidy-Moped


Mopidy-Mopify
=============

https://github.com/dirkgroenen/mopidy-mopify

A web client that uses external web services to provide additional features and
a more "complete" Spotify music experience. It's currently targeted at people
using Spotify through Mopidy. Made by Dirk Groenen.

.. image:: /ext/mopify.jpg
    :width: 696
    :height: 362

To install, run::

    pip install Mopidy-Mopify


Mopidy-MusicBox-Webclient
=========================

https://github.com/pimusicbox/mopidy-musicbox-webclient

The first web client for Mopidy, made with jQuery Mobile by Wouter van Wijk.
Also the web client used for Wouter's popular `Pi Musicbox
<https://www.pimusicbox.com/>`_ image for Raspberry Pi.

.. image:: /ext/musicbox_webclient.jpg
    :width: 696
    :height: 384

To install, run::

    pip install Mopidy-MusicBox-Webclient


Mopidy-Party
============

https://github.com/Lesterpig/mopidy-party

Minimal web client designed for collaborative music management during parties.

.. image:: /ext/mopidy_party.jpg

To install, run::

    pip install Mopidy-Party


Mopidy-Simple-Webclient
=======================

https://github.com/xolox/mopidy-simple-webclient

A minimalistic web client targeted for mobile devices. Made with jQuery and
Bootstrap by Peter Odding.

.. image:: /ext/simple_webclient.jpg
    :width: 473
    :height: 373

To install, run::

    pip install Mopidy-Simple-Webclient


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

.. image:: /ext/mopster.jpg
    :width: 696
    :height: 343

To use, just visit http://mopster.urizen.pl/.


Mopidy-Jukepi
=============

https://github.com/meantimeit/jukepi

A Mopidy web client built with Backbone by connrs.

.. image:: /ext/mopidy_jukepi.jpg
    :width: 696
    :height: 531

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
