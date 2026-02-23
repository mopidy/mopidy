
# Extensions

Mopidy's functionality can be extended with *extensions* — Python packages that
add one or more backends, frontends, mixers, or web clients to Mopidy.

Browse the [extension registry](https://mopidy.com/ext/) to find extensions for
music services like Spotify, SoundCloud, and YouTube, as well as clients,
scrobblers, and more.

If you want to build your own extension, see
[Extension development](../guides/extensiondev.md).

## Bundled extensions

Mopidy ships with a small set of extensions included out of the box:

- [mopidy-file](file.md) — play music from your local file system.
- [mopidy-m3u](m3u.md) — read and write M3U playlists stored on disk.
- [mopidy-stream](stream.md) — play streaming music and Internet radio.
- [mopidy-http](http.md) — control Mopidy from a web client over HTTP and WebSockets.
- [mopidy-softwaremixer](softwaremixer.md) — control audio volume in software through GStreamer.
