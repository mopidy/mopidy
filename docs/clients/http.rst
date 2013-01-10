.. _http-clients:

************
HTTP clients
************

Mopidy added an :ref:`HTTP frontend <http-frontend>` in 0.10 which provides the
building blocks needed for creating web clients for Mopidy with the help of a
WebSocket and a JavaScript library provided by Mopidy.

This page will list any HTTP/web Mopidy clients. If you've created one, please
notify us so we can include your client on this page.

See :ref:`http-frontend` for details on how to build your own web client.


woutervanwijk/Mopidy-Webclient
==============================

.. image:: /_static/woutervanwijk-mopidy-webclient.png
    :width: 410
    :height: 511

The first web client for Mopidy is still under development, but is already very
usable. It targets both desktop and mobile browsers.

To try it out, get a copy of https://github.com/woutervanwijk/Mopidy-WebClient
and point the :attr:`mopidy.settings.HTTP_SERVER_STATIC_DIR` setting towards
your copy of the web client.


Rompr
=====

.. image:: /_static/rompr.png
    :width: 557
    :height: 600

`Rompr <http://sourceforge.net/projects/rompr/>`_ is a web based MPD client.
`mrvanes <https://github.com/mrvanes>`, a Mopidy and Rompr user, said: "These
projects are a real match made in heaven."
