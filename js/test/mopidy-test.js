/*global require:false, assert:false, refute:false*/

if (typeof module === "object" && typeof require === "function") {
    var buster = require("buster");
    var Mopidy = require("../src/mopidy").Mopidy;
    var when = require("when");
}

buster.testCase("Mopidy", {
    setUp: function () {
        // Sinon.JS doesn't manage to stub PhantomJS' WebSocket implementation,
        // so we replace it with a dummy temporarily.
        var fakeWebSocket = function () {
            return {
                send: function () {},
                close: function () {}
            };
        };
        fakeWebSocket.CONNECTING = 0;
        fakeWebSocket.OPEN = 1;
        fakeWebSocket.CLOSING = 2;
        fakeWebSocket.CLOSED = 3;

        this.realWebSocket = Mopidy.WebSocket;
        Mopidy.WebSocket = fakeWebSocket;

        this.webSocketConstructorStub = this.stub(Mopidy, "WebSocket");

        this.webSocket = {
            close: this.stub(),
            send: this.stub()
        };
        this.mopidy = new Mopidy({webSocket: this.webSocket});
    },

    tearDown: function () {
        Mopidy.WebSocket = this.realWebSocket;
    },

    "constructor": {
        "connects when autoConnect is true": function () {
            new Mopidy({autoConnect: true});

            var currentHost = typeof document !== "undefined" &&
                document.location.host || "localhost";

            assert.calledOnceWith(this.webSocketConstructorStub,
                "ws://" + currentHost + "/mopidy/ws/");
        },

        "does not connect when autoConnect is false": function () {
            new Mopidy({autoConnect: false});

            refute.called(this.webSocketConstructorStub);
        },

        "does not connect when passed a WebSocket": function () {
            new Mopidy({webSocket: {}});

            refute.called(this.webSocketConstructorStub);
        },

        "works without 'new' keyword": function () {
            var mopidyConstructor = Mopidy; // To trick jshint into submission

            var mopidy = mopidyConstructor({webSocket: {}});

            assert.isObject(mopidy);
            assert(mopidy instanceof Mopidy);
        }
    },

    ".connect": {
        "connects when autoConnect is false": function () {
            var mopidy = new Mopidy({autoConnect: false});
            refute.called(this.webSocketConstructorStub);

            mopidy.connect();

            var currentHost = typeof document !== "undefined" &&
                document.location.host || "localhost";

            assert.calledOnceWith(this.webSocketConstructorStub,
                "ws://" + currentHost + "/mopidy/ws/");
        },

        "does nothing when the WebSocket is open": function () {
            this.webSocket.readyState = Mopidy.WebSocket.OPEN;
            var mopidy = new Mopidy({webSocket: this.webSocket});

            mopidy.connect();

            refute.called(this.webSocket.close);
            refute.called(this.webSocketConstructorStub);
        }
    },

    "WebSocket events": {
        "emits 'websocket:close' when connection is closed": function () {
            var spy = this.spy();
            this.mopidy.off("websocket:close");
            this.mopidy.on("websocket:close", spy);

            var closeEvent = {};
            this.webSocket.onclose(closeEvent);

            assert.calledOnceWith(spy, closeEvent);
        },

        "emits 'websocket:error' when errors occurs": function () {
            var spy = this.spy();
            this.mopidy.off("websocket:error");
            this.mopidy.on("websocket:error", spy);

            var errorEvent = {};
            this.webSocket.onerror(errorEvent);

            assert.calledOnceWith(spy, errorEvent);
        },

        "emits 'websocket:incomingMessage' when a message arrives": function () {
            var spy = this.spy();
            this.mopidy.off("websocket:incomingMessage");
            this.mopidy.on("websocket:incomingMessage", spy);

            var messageEvent = {data: "this is a message"};
            this.webSocket.onmessage(messageEvent);

            assert.calledOnceWith(spy, messageEvent);
        },

        "emits 'websocket:open' when connection is opened": function () {
            var spy = this.spy();
            this.mopidy.off("websocket:open");
            this.mopidy.on("websocket:open", spy);

            this.webSocket.onopen();

            assert.calledOnceWith(spy);
        }
    },

    "._cleanup": {
        setUp: function () {
            this.mopidy.off("state:offline");
        },

        "is called on 'websocket:close' event": function () {
            var closeEvent = {};
            var stub = this.stub(this.mopidy, "_cleanup");
            this.mopidy._delegateEvents();

            this.mopidy.emit("websocket:close", closeEvent);

            assert.calledOnceWith(stub, closeEvent);
        },

        "rejects all pending requests": function (done) {
            var closeEvent = {};
            assert.equals(Object.keys(this.mopidy._pendingRequests).length, 0);

            var promise1 = this.mopidy._send({method: "foo"});
            var promise2 = this.mopidy._send({method: "bar"});
            assert.equals(Object.keys(this.mopidy._pendingRequests).length, 2);

            this.mopidy._cleanup(closeEvent);

            assert.equals(Object.keys(this.mopidy._pendingRequests).length, 0);
            when.join(promise1, promise2).then(done(function () {
                assert(false, "Promises should be rejected");
            }), done(function (error) {
                assert.equals(error.message, "WebSocket closed");
                assert.same(error.closeEvent, closeEvent);
            }));
        },

        "emits 'state:offline' event when done": function () {
            var spy = this.spy();
            this.mopidy.on("state:offline", spy);

            this.mopidy._cleanup({});

            assert.calledOnceWith(spy);
        }
    },

    "._reconnect": {
        "is called when the state changes to offline": function () {
            var stub = this.stub(this.mopidy, "_reconnect");
            this.mopidy._delegateEvents();

            this.mopidy.emit("state:offline");

            assert.calledOnceWith(stub);
        },

        "tries to connect after an increasing backoff delay": function () {
            var clock = this.useFakeTimers();
            var connectStub = this.stub(this.mopidy, "connect");
            var pendingSpy = this.spy();
            this.mopidy.on("reconnectionPending", pendingSpy);
            var reconnectingSpy = this.spy();
            this.mopidy.on("reconnecting", reconnectingSpy);

            refute.called(connectStub);

            this.mopidy._reconnect();
            assert.calledOnceWith(pendingSpy, {timeToAttempt: 1000});
            clock.tick(0);
            refute.called(connectStub);
            clock.tick(1000);
            assert.calledOnceWith(reconnectingSpy);
            assert.calledOnce(connectStub);

            pendingSpy.reset();
            reconnectingSpy.reset();
            this.mopidy._reconnect();
            assert.calledOnceWith(pendingSpy, {timeToAttempt: 2000});
            assert.calledOnce(connectStub);
            clock.tick(0);
            assert.calledOnce(connectStub);
            clock.tick(1000);
            assert.calledOnce(connectStub);
            clock.tick(1000);
            assert.calledOnceWith(reconnectingSpy);
            assert.calledTwice(connectStub);

            pendingSpy.reset();
            reconnectingSpy.reset();
            this.mopidy._reconnect();
            assert.calledOnceWith(pendingSpy, {timeToAttempt: 4000});
            assert.calledTwice(connectStub);
            clock.tick(0);
            assert.calledTwice(connectStub);
            clock.tick(2000);
            assert.calledTwice(connectStub);
            clock.tick(2000);
            assert.calledOnceWith(reconnectingSpy);
            assert.calledThrice(connectStub);
        },

        "tries to connect at least about once per minute": function () {
            var clock = this.useFakeTimers();
            var connectStub = this.stub(this.mopidy, "connect");
            var pendingSpy = this.spy();
            this.mopidy.on("reconnectionPending", pendingSpy);
            this.mopidy._backoffDelay = this.mopidy._settings.backoffDelayMax;

            refute.called(connectStub);

            this.mopidy._reconnect();
            assert.calledOnceWith(pendingSpy, {timeToAttempt: 64000});
            clock.tick(0);
            refute.called(connectStub);
            clock.tick(64000);
            assert.calledOnce(connectStub);

            pendingSpy.reset();
            this.mopidy._reconnect();
            assert.calledOnceWith(pendingSpy, {timeToAttempt: 64000});
            assert.calledOnce(connectStub);
            clock.tick(0);
            assert.calledOnce(connectStub);
            clock.tick(64000);
            assert.calledTwice(connectStub);
        }
    },

    "._resetBackoffDelay": {
        "is called on 'websocket:open' event": function () {
            var stub = this.stub(this.mopidy, "_resetBackoffDelay");
            this.mopidy._delegateEvents();

            this.mopidy.emit("websocket:open");

            assert.calledOnceWith(stub);
        },

        "resets the backoff delay to the minimum value": function () {
            this.mopidy._backoffDelay = this.mopidy._backoffDelayMax;

            this.mopidy._resetBackoffDelay();

            assert.equals(this.mopidy._backoffDelay,
                 this.mopidy._settings.backoffDelayMin);
        }
    },

    "close": {
        "unregisters reconnection hooks": function () {
            this.stub(this.mopidy, "off");

            this.mopidy.close();

            assert.calledOnceWith(
                this.mopidy.off, "state:offline", this.mopidy._reconnect);
        },

        "closes the WebSocket": function () {
            this.mopidy.close();

            assert.calledOnceWith(this.mopidy._webSocket.close);
        }
    },

    "._handleWebSocketError": {
        "is called on 'websocket:error' event": function () {
            var error = {};
            var stub = this.stub(this.mopidy, "_handleWebSocketError");
            this.mopidy._delegateEvents();

            this.mopidy.emit("websocket:error", error);

            assert.calledOnceWith(stub, error);
        },

        "without stack logs the error to the console": function () {
            var stub = this.stub(this.mopidy._console, "warn");
            var error = {};

            this.mopidy._handleWebSocketError(error);

            assert.calledOnceWith(stub, "WebSocket error:", error);
        },

        "with stack logs the error to the console": function () {
            var stub = this.stub(this.mopidy._console, "warn");
            var error = {stack: "foo"};

            this.mopidy._handleWebSocketError(error);

            assert.calledOnceWith(stub, "WebSocket error:", error.stack);
        }
    },

    "._send": {
        "adds JSON-RPC fields to the message": function () {
            this.stub(this.mopidy, "_nextRequestId").returns(1);
            var stub = this.stub(JSON, "stringify");

            this.mopidy._send({method: "foo"});

            assert.calledOnceWith(stub, {
                jsonrpc: "2.0",
                id: 1,
                method: "foo"
            });
        },

        "adds a resolver to the pending requests queue": function () {
            this.stub(this.mopidy, "_nextRequestId").returns(1);
            assert.equals(Object.keys(this.mopidy._pendingRequests).length, 0);

            this.mopidy._send({method: "foo"});

            assert.equals(Object.keys(this.mopidy._pendingRequests).length, 1);
            assert.isFunction(this.mopidy._pendingRequests[1].resolve);
        },

        "sends message on the WebSocket": function () {
            refute.called(this.mopidy._webSocket.send);

            this.mopidy._send({method: "foo"});

            assert.calledOnce(this.mopidy._webSocket.send);
        },

        "emits a 'websocket:outgoingMessage' event": function () {
            var spy = this.spy();
            this.mopidy.on("websocket:outgoingMessage", spy);
            this.stub(this.mopidy, "_nextRequestId").returns(1);

            this.mopidy._send({method: "foo"});

            assert.calledOnceWith(spy, {
                jsonrpc: "2.0",
                id: 1,
                method: "foo"
            });
        },

        "immediately rejects request if CONNECTING": function (done) {
            this.mopidy._webSocket.readyState = Mopidy.WebSocket.CONNECTING;

            var promise = this.mopidy._send({method: "foo"});

            refute.called(this.mopidy._webSocket.send);
            promise.then(done(function () {
                assert(false);
            }), done(function (error) {
                assert.equals(
                    error.message, "WebSocket is still connecting");
            }));
        },

        "immediately rejects request if CLOSING": function (done) {
            this.mopidy._webSocket.readyState = Mopidy.WebSocket.CLOSING;

            var promise = this.mopidy._send({method: "foo"});

            refute.called(this.mopidy._webSocket.send);
            promise.then(done(function () {
                assert(false);
            }), done(function (error) {
                assert.equals(
                    error.message, "WebSocket is closing");
            }));
        },

        "immediately rejects request if CLOSED": function (done) {
            this.mopidy._webSocket.readyState = Mopidy.WebSocket.CLOSED;

            var promise = this.mopidy._send({method: "foo"});

            refute.called(this.mopidy._webSocket.send);
            promise.then(done(function () {
                assert(false);
            }), done(function (error) {
                assert.equals(
                    error.message, "WebSocket is closed");
            }));
        }
    },

    "._nextRequestId": {
        "returns an ever increasing ID": function () {
            var base = this.mopidy._nextRequestId();
            assert.equals(this.mopidy._nextRequestId(), base + 1);
            assert.equals(this.mopidy._nextRequestId(), base + 2);
            assert.equals(this.mopidy._nextRequestId(), base + 3);
        }
    },

    "._handleMessage": {
        "is called on 'websocket:incomingMessage' event": function () {
            var messageEvent = {};
            var stub = this.stub(this.mopidy, "_handleMessage");
            this.mopidy._delegateEvents();

            this.mopidy.emit("websocket:incomingMessage", messageEvent);

            assert.calledOnceWith(stub, messageEvent);
        },

        "passes JSON-RPC responses on to _handleResponse": function () {
            var stub = this.stub(this.mopidy, "_handleResponse");
            var message = {
                jsonrpc: "2.0",
                id: 1,
                result: null
            };
            var messageEvent = {data: JSON.stringify(message)};

            this.mopidy._handleMessage(messageEvent);

            assert.calledOnceWith(stub, message);
        },

        "passes events on to _handleEvent": function () {
            var stub = this.stub(this.mopidy, "_handleEvent");
            var message = {
                event: "track_playback_started",
                track: {}
            };
            var messageEvent = {data: JSON.stringify(message)};

            this.mopidy._handleMessage(messageEvent);

            assert.calledOnceWith(stub, message);
        },

        "logs unknown messages": function () {
            var stub = this.stub(this.mopidy._console, "warn");
            var messageEvent = {data: JSON.stringify({foo: "bar"})};

            this.mopidy._handleMessage(messageEvent);

            assert.calledOnceWith(stub,
                "Unknown message type received. Message was: " +
                messageEvent.data);
        },

        "logs JSON parsing errors": function () {
            var stub = this.stub(this.mopidy._console, "warn");
            var messageEvent = {data: "foobarbaz"};

            this.mopidy._handleMessage(messageEvent);

            assert.calledOnceWith(stub,
                "WebSocket message parsing failed. Message was: " +
                messageEvent.data);
        }
    },

    "._handleResponse": {
        "logs unexpected responses": function () {
            var stub = this.stub(this.mopidy._console, "warn");
            var responseMessage = {
                jsonrpc: "2.0",
                id: 1337,
                result: null
            };

            this.mopidy._handleResponse(responseMessage);

            assert.calledOnceWith(stub,
                "Unexpected response received. Message was:", responseMessage);
        },

        "removes the matching request from the pending queue": function () {
            assert.equals(Object.keys(this.mopidy._pendingRequests).length, 0);
            this.mopidy._send({method: "bar"});
            assert.equals(Object.keys(this.mopidy._pendingRequests).length, 1);

            this.mopidy._handleResponse({
                jsonrpc: "2.0",
                id: Object.keys(this.mopidy._pendingRequests)[0],
                result: "baz"
            });

            assert.equals(Object.keys(this.mopidy._pendingRequests).length, 0);
        },

        "resolves requests which get results back": function (done) {
            var promise = this.mopidy._send({method: "bar"});
            var responseResult = {};
            var responseMessage = {
                jsonrpc: "2.0",
                id: Object.keys(this.mopidy._pendingRequests)[0],
                result: responseResult
            };

            this.mopidy._handleResponse(responseMessage);
            promise.then(done(function (result) {
                assert.equals(result, responseResult);
            }), done(function () {
                assert(false);
            }));
        },

        "rejects and logs requests which get errors back": function (done) {
            var stub = this.stub(this.mopidy._console, "warn");
            var promise = this.mopidy._send({method: "bar"});
            var responseError = {message: "Error", data: {}};
            var responseMessage = {
                jsonrpc: "2.0",
                id: Object.keys(this.mopidy._pendingRequests)[0],
                error: responseError
            };

            this.mopidy._handleResponse(responseMessage);

            assert.calledOnceWith(stub,
                "Server returned error:", responseError);
            promise.then(done(function () {
                assert(false);
            }), done(function (error) {
                assert.equals(error, responseError);
            }));
        },

        "rejects and logs responses without result or error": function (done) {
            var stub = this.stub(this.mopidy._console, "warn");
            var promise = this.mopidy._send({method: "bar"});
            var responseMessage = {
                jsonrpc: "2.0",
                id: Object.keys(this.mopidy._pendingRequests)[0]
            };

            this.mopidy._handleResponse(responseMessage);

            assert.calledOnceWith(stub,
                "Response without 'result' or 'error' received. Message was:",
                responseMessage);
            promise.then(done(function () {
                assert(false);
            }), done(function (error) {
                assert.equals(
                    error.message,
                    "Response without 'result' or 'error' received");
                assert.equals(error.data.response, responseMessage);
            }));
        }
    },

    "._handleEvent": {
        "emits server side even on Mopidy object": function () {
            var spy = this.spy();
            this.mopidy.on(spy);
            var track = {};
            var message = {
                event: "track_playback_started",
                track: track
            };

            this.mopidy._handleEvent(message);

            assert.calledOnceWith(spy,
                "event:trackPlaybackStarted", {track: track});
        }
    },

    "._getApiSpec": {
        "is called on 'websocket:open' event": function () {
            var stub = this.stub(this.mopidy, "_getApiSpec");
            this.mopidy._delegateEvents();

            this.mopidy.emit("websocket:open");

            assert.calledOnceWith(stub);
        },

        "gets Api description from server and calls _createApi": function (done) {
            var methods = {};
            var sendStub = this.stub(this.mopidy, "_send");
            sendStub.returns(when.resolve(methods));
            var _createApiStub = this.stub(this.mopidy, "_createApi");

            this.mopidy._getApiSpec().then(done(function () {
                assert.calledOnceWith(sendStub, {method: "core.describe"});
                assert.calledOnceWith(_createApiStub, methods);
            }));
        }
    },

    "._createApi": {
        "can create an API with methods on the root object": function () {
            refute.defined(this.mopidy.hello);
            refute.defined(this.mopidy.hi);

            this.mopidy._createApi({
                hello: {
                    description: "Says hello",
                    params: []
                },
                hi: {
                    description: "Says hi",
                    params: []
                }
            });

            assert.isFunction(this.mopidy.hello);
            assert.equals(this.mopidy.hello.description, "Says hello");
            assert.equals(this.mopidy.hello.params, []);
            assert.isFunction(this.mopidy.hi);
            assert.equals(this.mopidy.hi.description, "Says hi");
            assert.equals(this.mopidy.hi.params, []);
        },

        "can create an API with methods on a sub-object": function () {
            refute.defined(this.mopidy.hello);

            this.mopidy._createApi({
                "hello.world": {
                    description: "Says hello to the world",
                    params: []
                }
            });

            assert.defined(this.mopidy.hello);
            assert.isFunction(this.mopidy.hello.world);
        },

        "strips off 'core' from method paths": function () {
            refute.defined(this.mopidy.hello);

            this.mopidy._createApi({
                "core.hello.world": {
                    description: "Says hello to the world",
                    params: []
                }
            });

            assert.defined(this.mopidy.hello);
            assert.isFunction(this.mopidy.hello.world);
        },

        "converts snake_case to camelCase": function () {
            refute.defined(this.mopidy.mightyGreetings);

            this.mopidy._createApi({
                "mighty_greetings.hello_world": {
                    description: "Says hello to the world",
                    params: []
                }
            });

            assert.defined(this.mopidy.mightyGreetings);
            assert.isFunction(this.mopidy.mightyGreetings.helloWorld);
        },

        "triggers 'state:online' event when API is ready for use": function () {
            var spy = this.spy();
            this.mopidy.on("state:online", spy);

            this.mopidy._createApi({});

            assert.calledOnceWith(spy);
        }
    }
});
