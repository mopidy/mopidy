# mopidy-m3u

mopidy-m3u is an extension for reading and writing M3U playlists stored
on disk. It is bundled with Mopidy and enabled by default.

This backend handles URIs starting with `m3u:`.

## Editing playlists

There is a core playlist API in place for editing playlists. This is supported
by a few Mopidy clients, but not through Mopidy's MPD server yet.

It is possible to edit playlists by editing the M3U files located in the
`m3u/playlists_dir` directory by hand with a text editor.
See [Wikipedia](https://en.wikipedia.org/wiki/M3U) for a short description
of the quite simple M3U playlist format.

If you run Mopidy manually in a terminal, the playlists are usually found in
`~/.local/share/mopidy/m3u/`.

If you run Mopidy as a system service, the playlists are usually found in
`/var/lib/mopidy/m3u/`.

## Configuration

See [Configuration](../usage/config.md) for general help on configuring Mopidy.

```ini title="mopidy.conf"
[m3u]
enabled = true
playlists_dir =
base_dir = $XDG_MUSIC_DIR
default_encoding = latin-1
default_extension = .m3u8
```

### m3u/enabled

If the M3U extension should be enabled or not.

### m3u/playlists_dir

Path to directory with M3U files. Unset by default, in which case the
extension's data dir is used to store playlists.

### m3u/base_dir

Path to base directory for resolving relative paths in M3U files.
If not set, relative paths are resolved based on the M3U file's
location.

### m3u/default_encoding

Text encoding used for files with extension `.m3u`. Default is
`latin-1`. Note that files with extension `.m3u8` are always
expected to be UTF-8 encoded.

### m3u/default_extension

The file extension for M3U playlists created using the core playlist
API. Default is `.m3u8`.
