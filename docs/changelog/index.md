
# Changelog

This changelog is used to track all major changes to Mopidy.

For older releases, see:
[Changelog 3.x](3.x.md) ·
[Changelog 2.x](2.x.md) ·
[Changelog 1.x](1.x.md) ·
[Changelog 0.x](0.x.md)

## v4.0.0 (UNRELEASED)

Mopidy 4.0 is a major release because we've dropped support for old versions of
our dependencies, removed a number of deprecated APIs, rebuilt both our data
models and app startup sequence, and migrated our docs to this new site.

### Dependencies

In general, we require the version of each dependency that is available in
the latest Debian stable release, Debian 13 Trixie.

- Python >= 3.13 is now required.
  Support for 3.7-3.12 has been dropped,
  while Python 3.13-3.14 has been added to the testing matrix.

- Replaced `pkg_resources` with `importlib.metadata` from Python's
  standard library, removing the runtime dependency on setuptools.

- GStreamer >= 1.26.2 is now required.

- PyGObject >= 3.50 is now an explicit Python dependency. Previously we assumed
  that you would install this together with your GStreamer installation.

- Pykka >= 4.1 is now required.

- Pydantic >= 2.10 is now required. This is a new dependency for Mopidy to
  replace our custom data models.

- Cyclopts >= 3.12 is now required. This is a new dependency for Mopidy to build
  the command line interfaces, replacing our use of `argparse`.

- Rich >= 3.9 is now required. This is a new dependency for Mopidy transitively
  via Cyclopts, which we've started to use directly as well to handle colorized
  log output.

- Requests >= 2.32 is now required.

- Tornado >= 6.4 is now required.

### Data models

Changes to the data models may affect any Mopidy extension or client.

- The `Track` and `Playlist` models now requires the `uri` field to always
  be set. (#2190, !2229)

- The models are now based on Pydantic data classes, which means:

    - All models fields and the `replace()` method should work as before, so
    unless your extension modifies or adds models, this should not affect you.

    - Models are now type-checked at runtime. This should help catch bugs early.

- Since we now use Pydantic to convert data models to and from JSON, the old
  model machinery has been removed. This includes the following:

    - `mopidy.models.ImmutableObject` — Not used by Mopidy since v1.0.5
    ten years ago.
    - `mopidy.models.ValidatedImmutableObject` — The old base class for
    all models.
    - `mopidy.models.ModelJSONEncoder`
    - `mopidy.models.model_json_decoder`
    - `mopidy.models.fields.Collection`
    - `mopidy.models.fields.Date`
    - `mopidy.models.fields.Field`
    - `mopidy.models.fields.Identifier`
    - `mopidy.models.fields.Integer`
    - `mopidy.models.fields.String`
    - `mopidy.models.fields.URI`

### Core API

Changes to the Core API may affect Mopidy clients.

Some of the changes in the Core API are related to replacing the use of
full `TlTrack` objects as API arguments with tracklist IDs, `tlid`.
This is especially relevant for remote clients, like web clients, which may
pass a lot less data over the network when using tracklist IDs in API calls.

- The core API is no longer exported from submodules, just from
  `mopidy.core`. Update your imports accordingly. (!2221)

    The removed modules are:

    - `mopidy.core.actor`
    - `mopidy.core.history`
    - `mopidy.core.library`
    - `mopidy.core.listener`
    - `mopidy.core.mixer`
    - `mopidy.core.playback`
    - `mopidy.core.playlists`
    - `mopidy.core.tracklist`

- Moved `mopidy.core.PlaybackState` to
  `mopidy.types.PlaybackState`.

#### Root object

- The `mopidy.core.Core` class now requires the `config` argument to be
  present. As this argument is provided by Mopidy itself at runtime, this
  should only affect the setup of extension's test suites.

#### Library controller

- No changes.

#### Playback controller

- `mopidy.core.PlaybackController.play`
  no longer accepts `TlTrack` objects,
  which has been deprecated since Mopidy 3.0.
  Use tracklist IDs (`tlid`) instead.
  (#1855, !2150)

#### Playlist controller

- No changes.

#### Tracklist controller

- No changes.

### Backend API

Changes to the Backend API may affect Mopidy backend extensions.

- Added `mopidy.backend.LibraryProvider.lookup_many` to take a list of
  URIs and return a mapping of URIs to tracks. If this method is not implemented
  then repeated calls to `mopidy.backend.LibraryProvider.lookup` will be
  used as a fallback.

- Deprecated `mopidy.backend.LibraryProvider.lookup`. Extensions should
  implement `mopidy.backend.LibraryProvider.lookup_many` instead.

### Audio API

Changes to the Audio API may affect a few Mopidy backend extensions.

- The old audio actor has been split into a `mopidy.audio.Audio`
  interface with the API used by core and backends, and a
  `mopidy.audio.GstAudio` implementation using GStreamer.
  The API is still very specific to GStreamer, but this split makes it a bit
  easier to mock out the audio layer in tests. (!2224)

- The audio API is no longer exported from submodules, just from
  `mopidy.audio`. Update your imports accordingly. The removed modules are:

    - `mopidy.audio.actor`
    - `mopidy.audio.listener`
    - `mopidy.audio.utils`

- Moved `mopidy.audio.PlaybackState` to
  `mopidy.types.PlaybackState`.

- The `mopidy.audio.tags.convert_tags_to_track` function now requires the
  track `uri` as an argument, so that it can construct valid
  `mopidy.models.Track` objects.

- Removed APIs only used by Mopidy-Spotify's bespoke audio delivery mechanism,
  which has not been used since Spotify shut down their libspotify APIs in
  May 2022. The removed functions/methods are:

    - `mopidy.audio.Audio.emit_data`
    - `mopidy.audio.Audio.set_appsrc`
    - `mopidy.audio.Audio.set_metadata`
    - `mopidy.audio.calculate_duration`
    - `mopidy.audio.create_buffer`
    - `mopidy.audio.millisecond_to_clocktime`

### Commands API

- Breaking change for extensions with their own CLI commands:

    The `mopidy.commands` module which extended on `argparse` to let
    extensions add their own CLI subcommands has been removed. We now use new
    dependency Cyclopts to build command line interfaces. The extensions
    maintained by the core team, including `mopidy-local` and
    `mopidy-spotify`, has been updated to use Cyclopts. The migration is pretty
    straight forward, but feel free to reach out for help with migrating your
    extension. (!2234)

### CLI

- Everything in the the app startup from CLI invocation to having a running
  server has been rebuilt. The code is now hopefully a lot easier to follow and
  maintain going forwards. (!2234)

- Previously, different commands had different default logging levels. Now all
  commands, including `mopidy` itself, only emits logs from warning level
  and higher by default. To decrease the logging level and get more verbose log
  output, add `-v` to the root command one or more times. (!2239)

- Support for custom log colors via the `logcolors` config section has
  been removed. Log output to terminals are now colorized using Rich, which
  hopefully leads to a more pleasant and readable log output. Log colors can
  still be disabled by changing `loggging/colors`. (!2241)

- The command `mopidy deps` no longer repeats transitive dependencies
  that have already been listed. This reduces the length of the command's output
  drastically. (!2152)

### Audio

- Workaround GStreamer `Gst.Structure().get_name()` regression for versions
  v1.26.0 to v1.26.2 (inclusive). (!2094)

### Type hints

- Added type hints to most of the source code. We now have a public
  `mopidy.types` module with types that are useful both for Mopidy core and
  extensions. This module will probably see tweaks going forward, and should not
  be considered entirely stable yet, but feel free to use the module's types in
  `if TYPE_CHECKING:` code blocks to aid the type checking of your extensions.

- Switched from mypy to pyright and ty for type checking. The jury is still out
  on which we'll use long-term. (!2226)

### Internals

- Dropped split between the `main` and `develop` branches in our development
  process. We now use `main` for all development, and have removed the
  `develop` branch.

- Moved bundled extensions to the private package `mopidy._exts`. (!2218)

    The removed modules are:

    - `mopidy.file`
    - `mopidy.http`
    - `mopidy.m3u`
    - `mopidy.softwaremixer`
    - `mopidy.stream`

- Renamed modules to be explicitly private. (!2227)

    The removed modules are:

    - `mopidy.config.keyring`
    - `mopidy.internal.*`
