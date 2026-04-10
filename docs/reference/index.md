# Reference

Only APIs documented here are public and open for use by Mopidy extensions.

- [mopidy command](command.md) — command-line reference for the `mopidy`
  executable.

## Concepts

- [Architecture](architecture.md) — how Mopidy's frontends, core, backends,
  and audio layer fit together.
- [Data models](models.md) — the immutable data objects passed between all
  layers of Mopidy.
- [Supporting types](types.md) — enumerations and other types used across the
  APIs.

## Framework APIs

- [Core API](core.md) — the main API used by frontends to control playback,
  manage the tracklist, and browse libraries.
- [Frontend API](frontend.md) — the interface for building frontends that
  react to playback events and control Mopidy.
- [Backend API](backend.md) — the interface for building backends that provide
  music libraries and playback.
- [Extension API](ext.md) — how extensions register themselves and expose
  configuration, actors, and commands.
- [Exceptions](exceptions.md) — exceptions raised by Mopidy's APIs.

## Web

- [HTTP server side API](http-server.md) — how extensions can serve static
  files or Tornado apps through Mopidy's built-in web server.
- [HTTP JSON-RPC API](http.md) — the JSON-RPC protocol for controlling Mopidy
  over HTTP and WebSockets.
- [Mopidy.js JavaScript library](js.md) — the official JavaScript client
  library wrapping the WebSocket API.

## Audio

- [Audio API](audio.md) — low-level audio playback control for backends.
- [Audio mixer API](mixer.md) — the interface for building mixer extensions
  that control volume.

## Utilities

- [Config API](config.md) — helpers for declaring and validating extension
  configuration.
- [HTTP client helpers](httpclient.md) — shared utilities for making HTTP
  requests from extensions, with proxy support.
- [Zeroconf API](zeroconf.md) — helpers for announcing services on the local
  network via DNS-SD/mDNS.
