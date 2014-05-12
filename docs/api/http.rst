.. _http-api:

********
HTTP API
********

The :ref:`ext-http` extension makes Mopidy's :ref:`core-api` available over
HTTP using WebSockets. We also provide a JavaScript wrapper, called
:ref:`Mopidy.js <mopidy-js>` around the HTTP API for use both from browsers and
Node.js.

.. warning:: API stability

    Since the HTTP API exposes our internal core API directly it is to be
    regarded as **experimental**. We cannot promise to keep any form of
    backwards compatibility between releases as we will need to change the core
    API while working out how to support new use cases. Thus, if you use this
    API, you must expect to do small adjustments to your client for every
    release of Mopidy.

    From Mopidy 1.0 and onwards, we intend to keep the core API far more
    stable.


.. _websocket-api:

WebSocket API
=============

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

    {"jsonrpc": "2.0", "id": 1, "result": {"__model__": "Track", "...": "..."}}

The JSON-RPC method ``core.describe`` returns a data structure describing all
available methods. If you're unsure how the core API maps to JSON-RPC, having a
look at the ``core.describe`` response can be helpful.


.. _mopidy-js:

Mopidy.js JavaScript library
============================

We've made a JavaScript library, Mopidy.js, which wraps the WebSocket and gets
you quickly started with working on your client instead of figuring out how to
communicate with Mopidy.


Getting the library for browser use
-----------------------------------

Regular and minified versions of Mopidy.js, ready for use, is installed
together with Mopidy. When the HTTP extension is enabled, the files are
available at:

- http://localhost:6680/mopidy/mopidy.js
- http://localhost:6680/mopidy/mopidy.min.js

You may need to adjust hostname and port for your local setup.

Thus, if you use Mopidy to host your web client, like described above, you can
load the latest version of Mopidy.js by adding the following script tag to your
HTML file:

.. code-block:: html

    <script type="text/javascript" src="/mopidy/mopidy.min.js"></script>

If you don't use Mopidy to host your web client, you can find the JS files in
the Git repo at:

- ``mopidy/http/data/mopidy.js``
- ``mopidy/http/data/mopidy.min.js``


Getting the library for Node.js use
-----------------------------------

If you want to use Mopidy.js from Node.js instead of a browser, you can install
Mopidy.js using npm::

    npm install mopidy

After npm completes, you can import Mopidy.js using ``require()``:

.. code-block:: js

    var Mopidy = require("mopidy");


Getting the library for development on the library
--------------------------------------------------

If you want to work on the Mopidy.js library itself, you'll find a complete
development setup in the ``js/`` dir in our repo. The instructions in
``js/README.md`` will guide you on your way.


Creating an instance
--------------------

Once you got Mopidy.js loaded, you need to create an instance of the wrapper:

.. code-block:: js

    var mopidy = new Mopidy();

When you instantiate ``Mopidy()`` without arguments, it will connect to
the WebSocket at ``/mopidy/ws/`` on the current host. Thus, if you don't host
your web client using Mopidy's web server, or if you use Mopidy.js from a
Node.js environment, you'll need to pass the URL to the WebSocket end point:

.. code-block:: js

    var mopidy = new Mopidy({
        webSocketUrl: "ws://localhost:6680/mopidy/ws/"
    });

It is also possible to create an instance first and connect to the WebSocket
later:

.. code-block:: js

    var mopidy = new Mopidy({autoConnect: false});
    // ... do other stuff, like hooking up events ...
    mopidy.connect();


Hooking up to events
--------------------

Once you have a Mopidy.js object, you can hook up to the events it emits. To
explore your possibilities, it can be useful to subscribe to all events and log
them:

.. code-block:: js

    mopidy.on(console.log.bind(console));

Several types of events are emitted:

- You can get notified about when the Mopidy.js object is connected to the
  server and ready for method calls, when it's offline, and when it's trying to
  reconnect to the server by looking at the events ``state:online``,
  ``state:offline``, ``reconnectionPending``, and ``reconnecting``.

- You can get events sent from the Mopidy server by looking at the events with
  the name prefix ``event:``, like ``event:trackPlaybackStarted``.

- You can introspect what happens internally on the WebSocket by looking at the
  events emitted with the name prefix ``websocket:``.

Mopidy.js uses the event emitter library `BANE
<https://github.com/busterjs/bane>`_, so you should refer to BANE's
short API documentation to see how you can hook up your listeners to the
different events.


Calling core API methods
------------------------

Once your Mopidy.js object has connected to the Mopidy server and emits the
``state:online`` event, it is ready to accept core API method calls:

.. code-block:: js

    mopidy.on("state:online", function () {
        mopidy.playback.next();
    });

Any calls you make before the ``state:online`` event is emitted will fail. If
you've hooked up an errback (more on that a bit later) to the promise returned
from the call, the errback will be called with an error message.

All methods in Mopidy's :ref:`core-api` is available via Mopidy.js. The core
API attributes is *not* available, but that shouldn't be a problem as we've
added (undocumented) getters and setters for all of them, so you can access the
attributes as well from JavaScript.

Both the WebSocket API and the JavaScript API are based on introspection of the
core Python API. Thus, they will always be up to date and immediately reflect
any changes we do to the core API.

The best way to explore the JavaScript API, is probably by opening your
browser's console, and using its tab completion to navigate the API. You'll
find the Mopidy core API exposed under ``mopidy.playback``,
``mopidy.tracklist``, ``mopidy.playlists``, and ``mopidy.library``.

All methods in the JavaScript API have an associated data structure describing
the Python params it expects, and most methods also have the Python API
documentation available. This is available right there in the browser console,
by looking at the method's ``description`` and ``params`` attributes:

.. code-block:: js

    console.log(mopidy.playback.next.params);
    console.log(mopidy.playback.next.description);

JSON-RPC 2.0 limits method parameters to be sent *either* by-position or
by-name. Combinations of both, like we're used to from Python, isn't supported
by JSON-RPC 2.0. To further limit this, Mopidy.js currently only supports
passing parameters by-position.

Obviously, you'll want to get a return value from many of your method calls.
Since everything is happening across the WebSocket and maybe even across the
network, you'll get the results asynchronously. Instead of having to pass
callbacks and errbacks to every method you call, the methods return "promise"
objects, which you can use to pipe the future result as input to another
method, or to hook up callback and errback functions.

.. code-block:: js

    var track = mopidy.playback.getCurrentTrack();
    // => ``track`` isn't a track, but a "promise" object

Instead, typical usage will look like this:

.. code-block:: js

    var printCurrentTrack = function (track) {
        if (track) {
            console.log("Currently playing:", track.name, "by",
                track.artists[0].name, "from", track.album.name);
        } else {
            console.log("No current track");
        }
    };

    mopidy.playback.getCurrentTrack().then(
        printCurrentTrack, console.error.bind(console));

The first function passed to ``then()``, ``printCurrentTrack``, is the callback
that will be called if the method call succeeds. The second function,
``console.error``, is the errback that will be called if anything goes wrong.
If you don't hook up an errback, debugging will be hard as errors will silently
go missing.

For debugging, you may be interested in errors from function without
interesting return values as well. In that case, you can pass ``null`` as the
callback:

.. code-block:: js

    mopidy.playback.next().then(null, console.error.bind(console));

The promise objects returned by Mopidy.js adheres to the `CommonJS Promises/A
<http://wiki.commonjs.org/wiki/Promises/A>`_ standard. We use the
implementation known as `when.js <https://github.com/cujojs/when>`_. Please
refer to when.js' documentation or the standard for further details on how to
work with promise objects.


Cleaning up
-----------

If you for some reason want to clean up after Mopidy.js before the web page is
closed or navigated away from, you can close the WebSocket, unregister all
event listeners, and delete the object like this:

.. code-block:: js

    // Close the WebSocket without reconnecting. Letting the object be garbage
    // collected will have the same effect, so this isn't strictly necessary.
    mopidy.close();

    // Unregister all event listeners. If you don't do this, you may have
    // lingering references to the object causing the garbage collector to not
    // clean up after it.
    mopidy.off();

    // Delete your reference to the object, so it can be garbage collected.
    mopidy = null;


Example to get started with
---------------------------

1. Make sure that you've installed all dependencies required by
   :ref:`ext-http`.

2. Create an empty directory for your web client.

3. Change the :confval:`http/static_dir` config value to point to your new
   directory.

4. Start/restart Mopidy.

5. Create a file in the directory named ``index.html`` containing e.g. "Hello,
   world!".

6. Visit http://localhost:6680/ to confirm that you can view your new HTML file
   there.

7. Include Mopidy.js in your web page:

   .. code-block:: html

       <script type="text/javascript" src="/mopidy/mopidy.min.js"></script>

8. Add one of the following Mopidy.js examples of how to queue and start
   playback of your first playlist either to your web page or a JavaScript file
   that you include in your web page.

   "Imperative" style:

   .. code-block:: js

        var consoleError = console.error.bind(console);

        var trackDesc = function (track) {
            return track.name + " by " + track.artists[0].name +
                " from " + track.album.name;
        };

        var queueAndPlayFirstPlaylist = function () {
            mopidy.playlists.getPlaylists().then(function (playlists) {
                var playlist = playlists[0];
                console.log("Loading playlist:", playlist.name);
                mopidy.tracklist.add(playlist.tracks).then(function (tlTracks) {
                    mopidy.playback.play(tlTracks[0]).then(function () {
                        mopidy.playback.getCurrentTrack().then(function (track) {
                            console.log("Now playing:", trackDesc(track));
                        }, consoleError);
                    }, consoleError);
                }, consoleError);
            }, consoleError);
        };

        var mopidy = new Mopidy();             // Connect to server
        mopidy.on(console.log.bind(console));  // Log all events
        mopidy.on("state:online", queueAndPlayFirstPlaylist);

   Approximately the same behavior in a more functional style, using chaining
   of promisies.

   .. code-block:: js

        var consoleError = console.error.bind(console);

        var getFirst = function (list) {
            return list[0];
        };

        var extractTracks = function (playlist) {
            return playlist.tracks;
        };

        var printTypeAndName = function (model) {
            console.log(model.__model__ + ": " + model.name);
            // By returning the playlist, this function can be inserted
            // anywhere a model with a name is piped in the chain.
            return model;
        };

        var trackDesc = function (track) {
            return track.name + " by " + track.artists[0].name +
                " from " + track.album.name;
        };

        var printNowPlaying = function () {
            // By returning any arguments we get, the function can be inserted
            // anywhere in the chain.
            var args = arguments;
            return mopidy.playback.getCurrentTrack().then(function (track) {
                console.log("Now playing:", trackDesc(track));
                return args;
            });
        };

        var queueAndPlayFirstPlaylist = function () {
            mopidy.playlists.getPlaylists()
                // => list of Playlists
                .then(getFirst, consoleError)
                // => Playlist
                .then(printTypeAndName, consoleError)
                // => Playlist
                .then(extractTracks, consoleError)
                // => list of Tracks
                .then(mopidy.tracklist.add, consoleError)
                // => list of TlTracks
                .then(getFirst, consoleError)
                // => TlTrack
                .then(mopidy.playback.play, consoleError)
                // => null
                .then(printNowPlaying, consoleError);
        };

        var mopidy = new Mopidy();             // Connect to server
        mopidy.on(console.log.bind(console));  // Log all events
        mopidy.on("state:online", queueAndPlayFirstPlaylist);

9. The web page should now queue and play your first playlist every time your
   load it. See the browser's console for output from the function, any errors,
   and all events that are emitted.

