.. _http-api:

*****************
HTTP JSON-RPC API
*****************

The :ref:`ext-http` extension makes Mopidy's :ref:`core-api` available using
JSON-RPC over HTTP using HTTP POST and WebSockets. We also provide a JavaScript
wrapper, called :ref:`Mopidy.js <mopidy-js>`, around the JSON-RPC over
WebSocket API for use both from browsers and Node.js. The
:ref:`http-explore-extension` extension, can also be used to get you
familiarized with HTTP based APIs.


.. _http-post-api:

HTTP POST API
=============

The Mopidy web server accepts HTTP requests with the POST method to
http://localhost:6680/mopidy/rpc, where the ``localhost:6680`` part will vary
with your local setup. The HTTP POST endpoint gives you access to Mopidy's
full core API, but does not give you notification on events. If you need
to listen to events, you should probably use the WebSocket API instead.

Example usage from the command line::

    $ curl -d '{"jsonrpc": "2.0", "id": 1, "method": "core.playback.get_state"}' http://localhost:6680/mopidy/rpc
    {"jsonrpc": "2.0", "id": 1, "result": "stopped"}

For details on the request and response format, see :ref:`json-rpc`.


.. _websocket-api:

WebSocket API
=============

The Mopidy web server exposes a WebSocket at http://localhost:6680/mopidy/ws,
where the ``localhost:6680`` part will vary with your local setup. The
WebSocket gives you access to Mopidy's full API and enables Mopidy to instantly
push events to the client, as they happen.

On the WebSocket we send two different kind of messages: The client can send
:ref:`JSON-RPC 2.0 requests <json-rpc>`, and the server will respond with
JSON-RPC 2.0 responses. In addition, the server will send :ref:`event messages
<json-events>` when something happens on the server. Both message types are
encoded as JSON objects.

If you're using the API from JavaScript, either in the browser or in Node.js,
you should use :ref:`mopidy-js` which wraps the WebSocket API in a nice
JavaScript API.


.. _json-rpc:

JSON-RPC 2.0 messages
=====================

JSON-RPC 2.0 messages can be recognized by checking for the key named
``jsonrpc`` with the string value ``2.0``. For details on the messaging format,
please refer to the `JSON-RPC 2.0 spec
<http://www.jsonrpc.org/specification>`_.

All methods in the :ref:`core-api` is made available through JSON-RPC calls
over the WebSocket. For example, :meth:`mopidy.core.PlaybackController.play` is
available as the JSON-RPC method ``core.playback.play``.

Example JSON-RPC request::

    {"jsonrpc": "2.0", "id": 1, "method": "core.playback.get_current_track"}

Example JSON-RPC response::

    {"jsonrpc": "2.0", "id": 1, "result": {"__model__": "Track", "...": "..."}}

The JSON-RPC method ``core.describe`` returns a data structure describing all
available methods. If you're unsure how the core API maps to JSON-RPC, having a
look at the ``core.describe`` response can be helpful.


.. _json-events:

Event messages
==============

Event objects will always have a key named ``event`` whose value is the event
type. Depending on the event type, the event may include additional fields for
related data. The events maps directly to the :class:`mopidy.core.CoreListener`
API. Refer to the :class:`~mopidy.core.CoreListener` method names is the
available event types. The :class:`~mopidy.core.CoreListener` method's keyword
arguments are all included as extra fields on the event objects. Example event
message::

    {"event": "track_playback_started", "track": {...}}
