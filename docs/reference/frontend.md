# Frontend API

The following requirements apply to frontends that run inside the Mopidy
process:

- A frontend MAY do mostly whatever it wants to, including creating threads,
  opening TCP ports and exposing Mopidy for a group of clients.

- A frontend MUST implement at least one [Pykka](https://pykka.readthedocs.io/)
  actor, called the "main actor" from here on.

- The main actor MUST accept two constructor arguments:

    - `config`, which is a dict structure with the entire Mopidy configuration.

    - `core`, which will be an `ActorProxy` for the core actor. This object gives
    access to the full [Core API](core.md).

- It MAY use additional actors to implement whatever it does, and using actors
  in frontend implementations is encouraged.

- The frontend is enabled if the extension it is part of is enabled. See
  [Extension development](../guides/extensiondev.md) for more information.

- The main actor MUST be able to start and stop the frontend when the main
  actor is started and stopped.

- The frontend MAY require additional config values to be set for it to work.

- Such config values MUST be documented.

- The main actor MUST raise the `mopidy.exceptions.FrontendError` with a
  descriptive error message if the defined config values are not adequate for
  the frontend to work properly.

- Any actor which is part of the frontend MAY implement the
  [mopidy.core.CoreListener][] interface to receive notification of the
  specified events.

## External frontends

A frontend that only needs the [Core API](core.md) can run as a separate
program and talk to Mopidy over the [WebSocket
API](http.md#websocket-api), which exposes the [Core API methods over
JSON-RPC](http.md#json-rpc-20-messages). This is a good fit for code that needs
special hardware access, such as GPIO, or raw memory, as it keeps that code out
of the Mopidy process, where it would run with Mopidy's privileges.

The WebSocket API speaks JSON-RPC 2.0, so an external frontend can be written
in any language. See [Mopidy.js](js.md) for the JavaScript client library. For
Python, [mopidyapi](https://github.com/AsbjornOlling/mopidyapi) is one community
client library, but it is not maintained by the Mopidy project.

The WebSocket API is provided by the bundled [mopidy-http](../ext/http.md)
extension, which is enabled by default.

## Frontend implementations

See the [extension registry](https://mopidy.com/ext/).
