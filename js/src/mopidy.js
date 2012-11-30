/*global bane:false, when:false*/

function Mopidy(settings) {
    var mopidy = this;

    mopidy._settings = settings || {};
    mopidy._settings.webSocketUrl =
        mopidy._settings.webSocketUrl ||
        "ws://" + document.location.host + "/mopidy/ws/";
    if (mopidy._settings.autoConnect !== false) {
        mopidy._settings.autoConnect = true;
    }
    mopidy._settings.backoffDelayMin = mopidy._settings.backoffDelayMin || 1000;
    mopidy._settings.backoffDelayMax = mopidy._settings.backoffDelayMax || 64000;

    mopidy._backoffDelay = mopidy._settings.backoffDelayMin;
    mopidy._pendingRequests = {};
    mopidy._webSocket = null;

    bane.createEventEmitter(mopidy);
    mopidy._delegateEvents();

    if (mopidy._settings.autoConnect) {
        mopidy._connect();
    }
}

Mopidy.prototype._delegateEvents = function () {
    var mopidy = this;

    // Remove existing event handlers
    mopidy.off("websocket:close");
    mopidy.off("websocket:error");
    mopidy.off("websocket:incomingMessage");
    mopidy.off("websocket:open");
    mopidy.off("state:offline");

    // Register basic set of event handlers
    mopidy.on("websocket:close", mopidy._cleanup);
    mopidy.on("websocket:error", mopidy._handleWebSocketError);
    mopidy.on("websocket:incomingMessage", mopidy._handleMessage);
    mopidy.on("websocket:open", mopidy._resetBackoffDelay);
    mopidy.on("websocket:open", mopidy._getApiSpec);
    mopidy.on("state:offline", mopidy._reconnect);
};

Mopidy.prototype._connect = function () {
    var mopidy = this;

    if (mopidy._webSocket) {
        if (mopidy._webSocket.readyState === WebSocket.OPEN) {
            return;
        } else {
            mopidy._webSocket.close();
        }
    }

    mopidy._webSocket = mopidy._settings.webSocket ||
        new WebSocket(mopidy._settings.webSocketUrl);

    mopidy._webSocket.onclose = function (close) {
        mopidy.emit("websocket:close", close);
    };

    mopidy._webSocket.onerror = function (error) {
        mopidy.emit("websocket:error", error);
    };

    mopidy._webSocket.onopen = function () {
        mopidy.emit("websocket:open");
    };

    mopidy._webSocket.onmessage = function (message) {
        mopidy.emit("websocket:incomingMessage", message);
    };
};

Mopidy.prototype._cleanup = function (closeEvent) {
    var mopidy = this;

    Object.keys(mopidy._pendingRequests).forEach(function (requestId) {
        var resolver = mopidy._pendingRequests[requestId];
        delete mopidy._pendingRequests[requestId];
        resolver.reject({
            message: "WebSocket closed",
            closeEvent: closeEvent
        });
    });

    mopidy.emit("state:offline");
};

Mopidy.prototype._reconnect = function () {
    var mopidy = this;

    mopidy.emit("reconnectionPending", {
        timeToAttempt: mopidy._backoffDelay
    });

    setTimeout(function () {
        mopidy.emit("reconnecting");
        mopidy._connect();
    }, mopidy._backoffDelay);

    mopidy._backoffDelay = mopidy._backoffDelay * 2;
    if (mopidy._backoffDelay > mopidy._settings.backoffDelayMax) {
        mopidy._backoffDelay = mopidy._settings.backoffDelayMax;
    }
};

Mopidy.prototype._resetBackoffDelay = function () {
    var mopidy = this;

    mopidy._backoffDelay = mopidy._settings.backoffDelayMin;
};

Mopidy.prototype._handleWebSocketError = function (error) {
    console.warn("WebSocket error:", error.stack || error);
};

Mopidy.prototype._send = function (message) {
    var mopidy = this;
    var deferred = when.defer();

    switch (mopidy._webSocket.readyState) {
    case WebSocket.CONNECTING:
        deferred.resolver.reject({
            message: "WebSocket is still connecting"
        });
        break;
    case WebSocket.CLOSING:
        deferred.resolver.reject({
            message: "WebSocket is closing"
        });
        break;
    case WebSocket.CLOSED:
        deferred.resolver.reject({
            message: "WebSocket is closed"
        });
        break;
    default:
        message.jsonrpc = "2.0";
        message.id = mopidy._nextRequestId();
        this._pendingRequests[message.id] = deferred.resolver;
        this._webSocket.send(JSON.stringify(message));
        mopidy.emit("websocket:outgoingMessage", message);
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
    var mopidy = this;

    try {
        var data = JSON.parse(message.data);
        if (data.hasOwnProperty("id")) {
            mopidy._handleResponse(data);
        } else if (data.hasOwnProperty("event")) {
            mopidy._handleEvent(data);
        } else {
            console.warn(
                "Unknown message type received. Message was: " +
                message.data);
        }
    } catch (error) {
        if (error instanceof SyntaxError) {
            console.warn(
                "WebSocket message parsing failed. Message was: " +
                message.data);
        } else {
            throw error;
        }
    }
};

Mopidy.prototype._handleResponse = function (responseMessage) {
    var mopidy = this;

    if (!mopidy._pendingRequests.hasOwnProperty(responseMessage.id)) {
        console.warn(
            "Unexpected response received. Message was:", responseMessage);
        return;
    }
    var resolver = mopidy._pendingRequests[responseMessage.id];
    delete mopidy._pendingRequests[responseMessage.id];

    if (responseMessage.hasOwnProperty("result")) {
        resolver.resolve(responseMessage.result);
    } else if (responseMessage.hasOwnProperty("error")) {
        resolver.reject(responseMessage.error);
        console.warn("Server returned error:", responseMessage.error);
    } else {
        resolver.reject({
            message: "Response without 'result' or 'error' received",
            data: {response: responseMessage}
        });
        console.warn(
            "Response without 'result' or 'error' received. Message was:",
            responseMessage);
    }
};

Mopidy.prototype._handleEvent = function (eventMessage) {
    var mopidy = this;

    var type = eventMessage.event;
    var data = eventMessage;
    delete data.event;

    mopidy.emit("event:" + mopidy._snakeToCamel(type), data); 
};

Mopidy.prototype._getApiSpec = function () {
    var mopidy = this;

    mopidy._send({method: "core.describe"})
        .then(mopidy._createApi.bind(mopidy), mopidy._handleWebSocketError)
        .then(null, mopidy._handleWebSocketError);
};

Mopidy.prototype._createApi = function (methods) {
    var mopidy = this;

    var caller = function (method) {
        return function () {
            var params = Array.prototype.slice.call(arguments);
            return mopidy._send({
                method: method,
                params: params
            });
        };
    };

    var getPath = function (fullName) {
        var path = fullName.split(".");
        if (path.length >= 1 && path[0] === "core") {
            path = path.slice(1);
        }
        return path;
    };

    var createObjects = function (objPath) {
        var parentObj = mopidy;
        objPath.forEach(function (objName) {
            objName = mopidy._snakeToCamel(objName);
            parentObj[objName] = parentObj[objName] || {};
            parentObj = parentObj[objName];
        });
        return parentObj;
    };

    var createMethod = function (fullMethodName) {
        var methodPath = getPath(fullMethodName);
        var methodName = mopidy._snakeToCamel(methodPath.slice(-1)[0]);
        var object = createObjects(methodPath.slice(0, -1));
        object[methodName] = caller(fullMethodName);
        object[methodName].description = methods[fullMethodName].description;
        object[methodName].params = methods[fullMethodName].params;
    };

    Object.keys(methods).forEach(createMethod);
    mopidy.emit("state:online");
};

Mopidy.prototype._snakeToCamel = function (name) {
    return name.replace(/(_[a-z])/g, function (match) {
        return match.toUpperCase().replace("_", "");
    });
};
