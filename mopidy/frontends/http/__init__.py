"""
The HTTP frontends lets you control Mopidy through HTTP and WebSockets, e.g.
from a web based client.

**Dependencies**

- ``cherrypy``

- ``ws4py``

**Settings**

- :attr:`mopidy.settings.HTTP_SERVER_HOSTNAME`

- :attr:`mopidy.settings.HTTP_SERVER_PORT`

- :attr:`mopidy.settings.HTTP_SERVER_STATIC_DIR`


Setup
=====

When this frontend is included in :attr:`mopidy.settings.FRONTENDS`, it starts
a web server at the port specified by :attr:`mopidy.settings.HTTP_SERVER_PORT`.

.. warning:: Security

    As a simple security measure, the web server is by default only available
    from localhost. To make it available from other computers, change
    :attr:`mopidy.settings.HTTP_SERVER_HOSTNAME`. Before you do so, note that
    the HTTP frontend does not feature any form of user authentication or
    authorization. Anyone able to access the web server can use the full core
    API of Mopidy. Thus, you probably only want to make the web server
    available from your local network or place it behind a web proxy which
    takes care or user authentication. You have been warned.


Using a web based Mopidy client
===============================

The web server can also host any static files, for example the HTML, CSS,
JavaScript, and images needed for a web based Mopidy client. To host static
files, change :attr:`mopidy.settings.HTTP_SERVER_STATIC_DIR` to point to the
root directory of your web client, e.g.::

    HTTP_SERVER_STATIC_DIR = u'/home/alice/dev/the-client'

If the directory includes a file named ``index.html``, it will be served on the
root of Mopidy's web server.

If you're making a web based client and wants to do server side development as
well, you are of course free to run your own web server and just use Mopidy's
web server for the APIs. But, for clients implemented purely in JavaScript,
letting Mopidy host the files is a simpler solution.


WebSocket API
=============

.. warning:: API stability

    Since this frontend exposes our internal core API directly it is to be
    regarded as **experimental**. We cannot promise to keep any form of
    backwards compatibility between releases as we will need to change the core
    API while working out how to support new use cases. Thus, if you use this
    API, you must expect to do small adjustments to your client for every
    release of Mopidy.

    From Mopidy 1.0 and onwards, we intend to keep the core API far more
    stable.

The web server exposes a WebSocket at ``/mopidy/ws/``. The WebSocket gives you
access to Mopidy's full API and enables Mopidy to instantly push events to the
client, as they happen.

On the WebSocket we send two different kind of messages: The client can send
JSON-RPC 2.0 requests, and the server will respond with JSON-RPC 2.0 responses.
In addition, the server will send event messages when something happens on the
server. Both message types are encoded as JSON objects.


Event messages
--------------

Event objects will always have a key named ``event`` whose value is the event
type. Depending on the event type, the event may include additional fields for
related data. The events maps directly to the :class:`mopidy.core.CoreListener`
API. Refer to the ``CoreListener`` method names is the available event types.
The ``CoreListener`` method's keyword arguments are all included as extra
fields on the event objects. Example event message::

    {"event": "track_playback_started", "track": {...}}


JSON-RPC 2.0 messaging
----------------------

JSON-RPC 2.0 messages can be recognized by checking for the key named
``jsonrpc`` with the string value ``2.0``. For details on the messaging format,
please refer to the `JSON-RPC 2.0 spec
<http://www.jsonrpc.org/specification>`_.

All methods (not attributes) in the :ref:`core-api` is made available through
JSON-RPC calls over the WebSocket. For example,
:meth:`mopidy.core.PlaybackController.play` is available as the JSON-RPC method
``core.playback.play``.

The core API's attributes is made available through setters and getters. For
example, the attribute :attr:`mopidy.core.PlaybackController.current_track` is
available as the JSON-RPC method ``core.playback.get_current_track``.

Example JSON-RPC request::

    {"jsonrpc": "2.0", "id": 1, "method": "core.playback.get_current_track"}

Example JSON-RPC response::

    {"jsonrpc": "2.0", "id": 1, "result": {"__model__": "Track", ...}}

The JSON-RPC method ``core.describe`` returns a data structure describing all
available methods. If you're unsure how the core API maps to JSON-RPC, having a
look at the ``core.describe`` response can be helpful.

JavaScript wrapper
==================

A JavaScript library wrapping the JSON-RPC over WebSocket API is under
development. Details on it will appear here when it's released.
"""

# flake8: noqa
from .actor import HttpFrontend
