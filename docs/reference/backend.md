# Backend API

The backend API is the interface that must be implemented when you create a
backend. If you are working on a frontend and need to access the backends, see
the [Core API](core.md) instead.

## URIs and routing of requests to the backend

When Mopidy's core layer is processing a client request, it routes the request
to one or more appropriate backends based on the URIs of the objects the
request touches on. The objects' URIs are compared with the backends'
[mopidy.backend.Backend.uri_schemes][] to select the relevant backends.

An often used pattern when implementing Mopidy backends is to create your own
URI scheme which you use for all tracks, playlists, etc. related to your
backend. In most cases the Mopidy URI is translated to an actual URI that
GStreamer knows how to play right before playback. For example:

- Spotify already has its own URI scheme (`spotify:track:...`,
  `spotify:playlist:...`, etc.) used throughout their applications, and thus
  mopidy-spotify simply uses the same URI scheme.

- mopidy-soundcloud created it's own URI scheme, after the model of Spotify,
  and uses URIs of the following forms: `soundcloud:search`,
  `soundcloud:user-...`, `soundcloud:exp-...`, and `soundcloud:set-...`.
  Playback is handled by converting the custom `soundcloud:..` URIs to
  `http://` URIs immediately before they are passed on to GStreamer for
  playback.

- Mopidy differentiates between `file://...` URIs handled by
  [mopidy-stream](../ext/stream.md) and `local:...` URIs handled by
  mopidy-local. [mopidy-stream](../ext/stream.md) can play `file://...` URIs
  pointing to tracks and playlists located anywhere on your system, but it
  doesn't know a thing about the object before you play it. On the other hand,
  mopidy-local scans a predefined `local/media_dir` to build a meta data
  library of all known tracks. It is thus limited to playing tracks residing in
  the media library, but can provide additional features like directory browsing
  and search. In other words, we have two different ways of playing local music,
  handled by two different backends, and have thus created two different URI
  schemes to separate their handling. The `local:...` URIs are converted to
  `file://...` URIs immediately before they are passed on to GStreamer for
  playback.

If there isn't an existing URI scheme that fits for your backend's purpose,
you should create your own, and name it after your extension's
`mopidy.ext.Extension.ext_name`. Care should be taken not to conflict with
already in use URI schemes. It is also recommended to design the format such
that tracks, playlists and other entities can be distinguished easily.

However, it's important to note that outside of the backend that created them,
URIs are opaque values that neither Mopidy's core layer or Mopidy frontends
should attempt to derive any meaning from. The only valid exception to this is
checking the scheme.

## Backend implementations

See the [extension registry](https://mopidy.com/ext/).

::: mopidy.backend
    options:
      heading_level: 2
