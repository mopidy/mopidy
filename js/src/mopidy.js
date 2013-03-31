/*global exports:false, require:false*/

if (typeof module === "object" && typeof require === "function") {
    var bane = require("bane");
    var websocket = require("faye-websocket");
    var when = require("when");
}

function Mopidy(settings) {
    if (!(this instanceof Mopidy)) {
        return new Mopidy(settings);
    }

    this._settings = this._configure(settings || {});
    this._console = this._getConsole();

    this._backoffDelay = this._settings.backoffDelayMin;
    this._pendingRequests = {};
    this._webSocket = null;

    bane.createEventEmitter(this);
    this._delegateEvents();

    if (this._settings.autoConnect) {
        this.connect();
    }
}

if (typeof module === "object" && typeof require === "function") {
    Mopidy.WebSocket = websocket.Client;
} else {
    Mopidy.WebSocket = window.WebSocket;
}

Mopidy.prototype._configure = function (settings) {
    var currentHost = (typeof document !== "undefined" &&
        document.location.host) || "localhost";
    settings.webSocketUrl = settings.webSocketUrl ||
        "ws://" + currentHost + "/mopidy/ws/";

    if (settings.autoConnect !== false) {
        settings.autoConnect = true;
    }

    settings.backoffDelayMin = settings.backoffDelayMin || 1000;
    settings.backoffDelayMax = settings.backoffDelayMax || 64000;

    return settings;
};

Mopidy.prototype._getConsole = function () {
    var console = typeof console !== "undefined" && console || {};

    console.log = console.log || function () {};
    console.warn = console.warn || function () {};
    console.error = console.error || function () {};

    return console;
};

Mopidy.prototype._delegateEvents = function () {
    // Remove existing event handlers
    this.off("websocket:close");
    this.off("websocket:error");
    this.off("websocket:incomingMessage");
    this.off("websocket:open");
    this.off("state:offline");

    // Register basic set of event handlers
    this.on("websocket:close", this._cleanup);
    this.on("websocket:error", this._handleWebSocketError);
    this.on("websocket:incomingMessage", this._handleMessage);
    this.on("websocket:open", this._resetBackoffDelay);
    this.on("websocket:open", this._getApiSpec);
    this.on("state:offline", this._reconnect);
};

Mopidy.prototype.connect = function () {
    if (this._webSocket) {
        if (this._webSocket.readyState === Mopidy.WebSocket.OPEN) {
            return;
        } else {
            this._webSocket.close();
        }
    }

    this._webSocket = this._settings.webSocket ||
        new Mopidy.WebSocket(this._settings.webSocketUrl);

    this._webSocket.onclose = function (close) {
        this.emit("websocket:close", close);
    }.bind(this);

    this._webSocket.onerror = function (error) {
        this.emit("websocket:error", error);
    }.bind(this);

    this._webSocket.onopen = function () {
        this.emit("websocket:open");
    }.bind(this);

    this._webSocket.onmessage = function (message) {
        this.emit("websocket:incomingMessage", message);
    }.bind(this);
};

Mopidy.prototype._cleanup = function (closeEvent) {
    Object.keys(this._pendingRequests).forEach(function (requestId) {
        var resolver = this._pendingRequests[requestId];
        delete this._pendingRequests[requestId];
        resolver.reject({
            message: "WebSocket closed",
            closeEvent: closeEvent
        });
    }.bind(this));

    this.emit("state:offline");
};

Mopidy.prototype._reconnect = function () {
    this.emit("reconnectionPending", {
        timeToAttempt: this._backoffDelay
    });

    setTimeout(function () {
        this.emit("reconnecting");
        this.connect();
    }.bind(this), this._backoffDelay);

    this._backoffDelay = this._backoffDelay * 2;
    if (this._backoffDelay > this._settings.backoffDelayMax) {
        this._backoffDelay = this._settings.backoffDelayMax;
    }
};

Mopidy.prototype._resetBackoffDelay = function () {
    this._backoffDelay = this._settings.backoffDelayMin;
};

Mopidy.prototype.close = function () {
    this.off("state:offline", this._reconnect);
    this._webSocket.close();
};

Mopidy.prototype._handleWebSocketError = function (error) {
    this._console.warn("WebSocket error:", error.stack || error);
};

Mopidy.prototype._send = function (message) {
    var deferred = when.defer();

    switch (this._webSocket.readyState) {
    case Mopidy.WebSocket.CONNECTING:
        deferred.resolver.reject({
            message: "WebSocket is still connecting"
        });
        break;
    case Mopidy.WebSocket.CLOSING:
        deferred.resolver.reject({
            message: "WebSocket is closing"
        });
        break;
    case Mopidy.WebSocket.CLOSED:
        deferred.resolver.reject({
            message: "WebSocket is closed"
        });
        break;
    default:
        message.jsonrpc = "2.0";
        message.id = this._nextRequestId();
        this._pendingRequests[message.id] = deferred.resolver;
        this._webSocket.send(JSON.stringify(message));
        this.emit("websocket:outgoingMessage", message);
    }

    return deferred.promise;
};

Mopidy.prototype._nextRequestId = (function () {
    var lastUsed = -1;
    return function () {
        lastUsed += 1;
        return lastUsed;
    };
}());

Mopidy.prototype._handleMessage = function (message) {
    try {
        var data = JSON.parse(message.data);
        if (data.hasOwnProperty("id")) {
            this._handleResponse(data);
        } else if (data.hasOwnProperty("event")) {
            this._handleEvent(data);
        } else {
            this._console.warn(
                "Unknown message type received. Message was: " +
                message.data);
        }
    } catch (error) {
        if (error instanceof SyntaxError) {
            this._console.warn(
                "WebSocket message parsing failed. Message was: " +
                message.data);
        } else {
            throw error;
        }
    }
};

Mopidy.prototype._handleResponse = function (responseMessage) {
    if (!this._pendingRequests.hasOwnProperty(responseMessage.id)) {
        this._console.warn(
            "Unexpected response received. Message was:", responseMessage);
        return;
    }

    var resolver = this._pendingRequests[responseMessage.id];
    delete this._pendingRequests[responseMessage.id];

    if (responseMessage.hasOwnProperty("result")) {
        resolver.resolve(responseMessage.result);
    } else if (responseMessage.hasOwnProperty("error")) {
        resolver.reject(responseMessage.error);
        this._console.warn("Server returned error:", responseMessage.error);
    } else {
        resolver.reject({
            message: "Response without 'result' or 'error' received",
            data: {response: responseMessage}
        });
        this._console.warn(
            "Response without 'result' or 'error' received. Message was:",
            responseMessage);
    }
};

Mopidy.prototype._handleEvent = function (eventMessage) {
    var type = eventMessage.event;
    var data = eventMessage;
    delete data.event;

    this.emit("event:" + this._snakeToCamel(type), data);
};

Mopidy.prototype._getApiSpec = function () {
    return this._send({method: "core.describe"})
        .then(this._createApi.bind(this), this._handleWebSocketError)
        .then(null, this._handleWebSocketError);
};

Mopidy.prototype._createApi = function (methods) {
    var caller = function (method) {
        return function () {
            var params = Array.prototype.slice.call(arguments);
            return this._send({
                method: method,
                params: params
            });
        }.bind(this);
    }.bind(this);

    var getPath = function (fullName) {
        var path = fullName.split(".");
        if (path.length >= 1 && path[0] === "core") {
            path = path.slice(1);
        }
        return path;
    };

    var createObjects = function (objPath) {
        var parentObj = this;
        objPath.forEach(function (objName) {
            objName = this._snakeToCamel(objName);
            parentObj[objName] = parentObj[objName] || {};
            parentObj = parentObj[objName];
        }.bind(this));
        return parentObj;
    }.bind(this);

    var createMethod = function (fullMethodName) {
        var methodPath = getPath(fullMethodName);
        var methodName = this._snakeToCamel(methodPath.slice(-1)[0]);
        var object = createObjects(methodPath.slice(0, -1));
        object[methodName] = caller(fullMethodName);
        object[methodName].description = methods[fullMethodName].description;
        object[methodName].params = methods[fullMethodName].params;
    }.bind(this);

    Object.keys(methods).forEach(createMethod);
    this.emit("state:online");
};

Mopidy.prototype._snakeToCamel = function (name) {
    return name.replace(/(_[a-z])/g, function (match) {
        return match.toUpperCase().replace("_", "");
    });
};

if (typeof exports === "object") {
    exports.Mopidy = Mopidy;
}
