.. _mopidy-js:

****************************
Mopidy.js JavaScript library
****************************

We've made a JavaScript library, Mopidy.js, which wraps the
:ref:`websocket-api` and gets you quickly started with working on your client
instead of figuring out how to communicate with Mopidy.


Getting the library for browser use
===================================

Regular and minified versions of Mopidy.js, ready for use, is installed
together with Mopidy. When the HTTP extension is enabled, the files are
available at:

- http://localhost:6680/mopidy/mopidy.js
- http://localhost:6680/mopidy/mopidy.min.js

You may need to adjust hostname and port for your local setup.

Thus, if you use Mopidy to host your web client, like described in
:ref:`static-web-client`, you can load the latest version of Mopidy.js by
adding the following script tag to your HTML file:

.. code-block:: html

    <script type="text/javascript" src="/mopidy/mopidy.min.js"></script>

If you don't use Mopidy to host your web client, you can find the JS files in
the Git repo at:

- ``mopidy/http/data/mopidy.js``
- ``mopidy/http/data/mopidy.min.js``


Getting the library for Node.js or Browserify use
=================================================

If you want to use Mopidy.js from Node.js or on the web through Browserify, you
can install Mopidy.js using npm::

    npm install mopidy

After npm completes, you can import Mopidy.js using ``require()``:

.. code-block:: js

    var Mopidy = require("mopidy");


Getting the library for development on the library
==================================================

If you want to work on the Mopidy.js library itself, you'll find the source
code and a complete development setup in the `Mopidy.js Git repo
<https://github.com/mopidy/mopidy.js>`_. The instructions in ``README.md`` will
guide you on your way.


Creating an instance
====================

Once you have Mopidy.js loaded, you need to create an instance of the wrapper:

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

When creating an instance, you can specify the following settings:

``autoConnect``
    Whether or not to connect to the WebSocket on instance creation. Defaults
    to true.

``backoffDelayMin``
    The minimum number of milliseconds to wait after a connection error before
    we try to reconnect. For every failed attempt, the backoff delay is doubled
    until it reaches ``backoffDelayMax``. Defaults to 1000.

``backoffDelayMax``
    The maximum number of milliseconds to wait after a connection error before
    we try to reconnect. Defaults to 64000.

``callingConvention``
    Which calling convention to use when calling methods.

    If set to "by-position-only", methods expect to be called with positional
    arguments, like ``mopidy.foo.bar(null, true, 2)``.

    If set to "by-position-or-by-name", methods expect to be called either with
    an array of position arguments, like ``mopidy.foo.bar([null, true, 2])``,
    or with an object of named arguments, like ``mopidy.foo.bar({id: 2})``. The
    advantage of the "by-position-or-by-name" calling convention is that
    arguments with default values can be left out of the named argument object.
    Using named arguments also makes the code more readable, and more resistent
    to future API changes.

    .. note::

        For backwards compatibility, the default is "by-position-only". In the
        future, the default will change to "by-position-or-by-name". You should
        explicitly set this setting to your choice, so you won't be affected
        when the default changes.

    .. versionadded:: 0.19 (Mopidy.js 0.4)

``console``
    If set, this object will be used to log errors from Mopidy.js. This is
    mostly useful for testing Mopidy.js.

``webSocket``
    An existing WebSocket object to be used instead of creating a new
    WebSocket. Defaults to undefined.

``webSocketUrl``
    URL used when creating new WebSocket objects. Defaults to
    ``ws://<document.location.host>/mopidy/ws``, or
    ``ws://localhost/mopidy/ws`` if ``document.location.host`` isn't
    available, like it is in the browser environment.


Hooking up to events
====================

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
========================

Once your Mopidy.js object has connected to the Mopidy server and emits the
``state:online`` event, it is ready to accept core API method calls:

.. code-block:: js

    mopidy.on("state:online", function () {
        mopidy.playback.next();
    });

Any calls you make before the ``state:online`` event is emitted will fail. If
you've hooked up an errback (more on that a bit later) to the promise returned
from the call, the errback will be called with a ``Mopidy.ConnectionError``
instance.

All methods in Mopidy's :ref:`core-api` is available via Mopidy.js. For
example, the :meth:`mopidy.core.PlaybackController.get_state` method is
available in JSON-RPC as the method ``core.playback.get_state`` and in
Mopidy.js as ``mopidy.playback.getState()``.

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
by JSON-RPC 2.0.

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

    mopidy.playback.getCurrentTrack()
        .done(printCurrentTrack);

The function passed to ``done()``, ``printCurrentTrack``, is the callback
that will be called if the method call succeeds. If anything goes wrong,
``done()`` will throw an exception.

If you want to explicitly handle any errors and avoid an exception being
thrown, you can register an error handler function anywhere in a promise
chain. The function will be called with the error object as the only argument:

.. code-block:: js

    mopidy.playback.getCurrentTrack()
        .catch(console.error.bind(console))
        .done(printCurrentTrack);

You can also register the error handler at the end of the promise chain by
passing it as the second argument to ``done()``:

.. code-block:: js

    mopidy.playback.getCurrentTrack()
        .done(printCurrentTrack, console.error.bind(console));

If you don't hook up an error handler function and never call ``done()`` on the
promise object, warnings will be logged to the console complaining that you
have unhandled errors. In general, unhandled errors will not go silently
missing.

The promise objects returned by Mopidy.js adheres to the `CommonJS Promises/A
<http://wiki.commonjs.org/wiki/Promises/A>`_ standard. We use the
implementation known as `when.js <https://github.com/cujojs/when>`_, and
reexport it as ``Mopidy.when`` so you don't have to duplicate the dependency.
Please refer to when.js' documentation or the standard for further details on
how to work with promise objects.


Cleaning up
===========

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
===========================

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

        var trackDesc = function (track) {
            return track.name + " by " + track.artists[0].name +
                " from " + track.album.name;
        };

        var queueAndPlay = function (playlistNum, trackNum) {
            playlistNum = playlistNum || 0;
            trackNum = trackNum || 0;
            mopidy.playlists.getPlaylists().then(function (playlists) {
                var playlist = playlists[playlistNum];
                console.log("Loading playlist:", playlist.name);
                return mopidy.tracklist.add(playlist.tracks).then(function (tlTracks) {
                    return mopidy.playback.play(tlTracks[trackNum]).then(function () {
                        return mopidy.playback.getCurrentTrack().then(function (track) {
                            console.log("Now playing:", trackDesc(track));
                        });
                    });
                });
            })
            .catch(console.error.bind(console)) // Handle errors here
            .done();                            // ...or they'll be thrown here
        };

        var mopidy = new Mopidy();             // Connect to server
        mopidy.on(console.log.bind(console));  // Log all events
        mopidy.on("state:online", queueAndPlay);

   Approximately the same behavior in a more functional style, using chaining
   of promises.

   .. code-block:: js

        var get = function (key, object) {
            return object[key];
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
            return mopidy.playback.getCurrentTrack()
                .then(function (track) {
                    console.log("Now playing:", trackDesc(track));
                    return args;
                });
        };

        var queueAndPlay = function (playlistNum, trackNum) {
            playlistNum = playlistNum || 0;
            trackNum = trackNum || 0;
            mopidy.playlists.getPlaylists()
                // => list of Playlists
                .fold(get, playlistNum)
                // => Playlist
                .then(printTypeAndName)
                // => Playlist
                .fold(get, 'tracks')
                // => list of Tracks
                .then(mopidy.tracklist.add)
                // => list of TlTracks
                .fold(get, trackNum)
                // => TlTrack
                .then(mopidy.playback.play)
                // => null
                .then(printNowPlaying)
                // => null
                .catch(console.error.bind(console))  // Handle errors here
                // => null
                .done();                       // ...or they'll be thrown here
        };

        var mopidy = new Mopidy();             // Connect to server
        mopidy.on(console.log.bind(console));  // Log all events
        mopidy.on("state:online", queueAndPlay);

9. The web page should now queue and play your first playlist every time you
   load it. See the browser's console for output from the function, any errors,
   and all events that are emitted.
