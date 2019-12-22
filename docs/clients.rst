.. _clients:

*******
Clients
*******

Once Mopidy is up and running, you need a client to control it.

Note that clients only *control* Mopidy.
The audio itself is not streamed to the clients,
but it is played on the computer running Mopidy.
This is by design, as Mopidy was originally modelled after MPD.
If you want to stream audio from Mopidy to another device,
the primary options are :ref:`icecast` and `Snapcast`_.

The most popular ways to control Mopidy are with
web clients and with MPD clients.

In addition, alternative frontends like `Mopidy-MPRIS`_ and
`Mopidy-Raspberry-GPIO`_ provides additional ways to control Mopidy.
Alternative frontends that use a server-client architecture
usually list relevant clients in the extension's documentation.

.. _Mopidy-MPD: https://mopidy.com/ext/mpd/
.. _Mopidy-MPRIS: https://mopidy.com/ext/mpris/
.. _Mopidy-Raspberry-GPIO: https://mopidy.com/ext/raspberry-gpio/
.. _Snapcast: https://github.com/badaix/snapcast


.. _web-clients:

Web clients
===========

There are many clients available that use :ref:`ext-http` to control Mopidy.

Web extensions
--------------

Mopidy extensions can make additional web APIs available through
Mopidy's builtin web server by implementing the :ref:`http-server-api`.
Web clients can use the :ref:`http-api` to control Mopidy from JavaScript.

See the `Mopidy extension registry <https://mopidy.com/ext/>`_ to find a
number of web clients can be easily installed as Mopidy extensions.

Non-extension web clients
-------------------------

There are a few Mopidy web clients that are not installable as
Mopidy extensions:

- `Apollo Player <https://github.com/samcreate/Apollo-Player>`_
- `Mopster <https://github.com/cowbell/mopster>`_

Web-based MPD clients
---------------------

Lastly, there are several web based MPD clients, which doesn't use the
:ref:`ext-http` frontend at all, but connect to Mopidy through the
Mopidy-MPD frontend. For a list of those, see the "Web clients" section of the
`MPD wiki's clients list <https://mpd.fandom.com/wiki/Clients>`_.


.. _mpd-clients:

MPD clients
===========

MPD is the protocol used by the original MPD server project since 2003.
The `Mopidy-MPD`_ extension provides a server that implements
the same protocol, and is compatible with most MPD clients.

There are dozens of MPD clients available.
Please refer to the `Mopidy-MPD`_ extension's documentation for an overview.


.. _mpris-clients:

MPRIS clients
=============

MPRIS is a specification that describes a standard D-Bus interface
for making media players available to other applications on the same system.

See the `Mopidy-MPRIS`_ documentation for a survey of some MPRIS clients.
