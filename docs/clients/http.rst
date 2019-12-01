.. _http-clients:

************
HTTP clients
************

There are many clients available that use HTTP to control Mopidy.

Web extensions
==============

Mopidy extensions can make additional web interfaces available through
Mopidy's bundled web server by implementing the :ref:`http-server-api`.
Web clients can use the :ref:`http-api` to control Mopidy from JavaScript.

See the `Mopidy extension registry <https://mopidy.com/ext/>`_ to find a
number of web clients can be installed as Mopidy extensions with ``pip``.

Non-extension web clients
=========================

There are a few Mopidy web clients that are not installable as
Mopidy extensions:

- `Apollo Player <https://github.com/samcreate/Apollo-Player>`_
- `Mopster <https://github.com/cowbell/mopster>`_

Web-based MPD clients
=====================

In addition, there are several web based MPD clients, which doesn't use the
:ref:`ext-http` frontend at all, but connect to Mopidy through our
:ref:`ext-mpd` frontend. For a list of those, see :ref:`mpd-web-clients`.
