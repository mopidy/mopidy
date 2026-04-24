# Changelog

This changelog is used to track all major changes to Mopidy.

For older releases, see:
[Changelog 3.x](3.x.md) ·
[Changelog 2.x](2.x.md) ·
[Changelog 1.x](1.x.md) ·
[Changelog 0.x](0.x.md)

## v4.0.0 (2026-04-25)

Mopidy 4.0 is a major release bringing very few functional changes, but mostly
focusing on modernizations to Mopidy's tech stack to keep it maintainable going
into the future. In Mopidy 4.0 we've:

- dropped support for old versions of our dependencies,
- rebuilt data models using Pydantic, so data is validated and errors are caught
  at the edges of the application instead of on use,
- removed a few long-deprecated APIs,
- rebuilt the app startup sequence,
- made many modules explicitly private,
- added type hints to most of the source code, and
- rebuilt our docs using Zensical.

### Dependencies

We require newer versions of all of our dependencies. The versions we require
are all available in Debian 13 Trixie, which is the latest Debian stable release
at the time of writing.

- Python >= 3.13

    - Support for 3.7-3.12 has been dropped. Python 3.13-3.14 has been added to
      the testing matrix.

    - setuptools is no longer a runtime dependency, as we've replaced the use of
      `pkg_resources` with `importlib.metadata` from Python's standard library.

- GStreamer >= 1.26.2

    - PyGObject >= 3.50 is now an explicit Python dependency. Previously we
      assumed that you would install this together with your GStreamer
      installation.

    - Added a workaround for GStreamer's `Gst.Structure().get_name()` regression
      for versions v1.26.1 to v1.26.2 inclusive. (!2094)

    - We also added a workaround to not crash when using PyGObject < 3.55.3
      together with GLib >= 2.88. (!2248)

- Pykka >= 4.1

- Tornado >= 6.4

- Pydantic >= 2.10

    - This is a new dependency for Mopidy to replace our custom data models.

- Cyclopts >= 3.12

    - This is a new dependency for Mopidy to build the command line interfaces,
      replacing our use of `argparse`.

- Rich >= 3.9

    - This is a new dependency for Mopidy transitively via Cyclopts, which we've
      started to use directly as well to handle colorized log output.

- HTTPX >= 0.28.1

    - HTTPX has replaced Requests as our HTTP client. (!2249)

### CLI

- Everything in the app startup from starting Mopidy to having a running server
  has been rebuilt. The code is now hopefully a lot easier to follow and
  maintain going forwards. (!2234)

- Breaking change for extensions with their own CLI commands:

    The `mopidy.commands` module which extended on `argparse` to let
    extensions add their own CLI subcommands has been removed. We now use new
    dependency Cyclopts to build command line interfaces.

    The extensions maintained by the core team, including `mopidy-local` and
    `mopidy-spotify`, have been updated to use Cyclopts. The migration is pretty
    straight forward, but feel free to reach out for help with migrating your
    extension. (!2234)

- Previously, different commands had different default logging levels. Now all
  commands, including `mopidy` itself, emit logs from warning level and higher
  by default. To get more detailed log output, add `-v` to the root command one
  or more times. The included `mopidy.service` systemd unit has been updated to
  include `--verbose` in its command, to continue logging on info level. (!2239)

- Support for custom log colors via the `logcolors` config section has
  been removed. (!2241)

- Log output to terminals are now colorized using Rich, which hopefully leads to
  a more pleasant and readable log output. Log colors can still be disabled by
  changing the `logging/colors` config. (!2241)

- The command `mopidy deps` no longer repeats transitive dependencies
  that have already been listed. This reduces the length of the command's output
  drastically. (!2152)

### Data models

Changes to the data models may affect any Mopidy extension or client.

- The [`Track`][mopidy.models.Track] and [`Playlist`][mopidy.models.Playlist]
  models now require the `uri` field to always be set. (#2190, !2229)

- The models are now based on Pydantic data classes, which means:

    - All model fields and the [`replace()`][mopidy.models.Album.replace] method
      should work as before, so unless your extension modifies or adds models,
      this should not affect you.

    - Models are now type-checked at runtime. This should help catch bugs early,
      where the models are instantiated with data, instead of when the data is
      used. This means that if your extension is instantiating models with
      incorrect data, you should see errors sooner than before.

- Since we now use Pydantic to convert data models to and from JSON, the old
  model machinery has been removed. This includes the following:

    - `mopidy.models.ImmutableObject`
    - `mopidy.models.ValidatedImmutableObject`
    - `mopidy.models.ModelJSONEncoder`
    - `mopidy.models.model_json_decoder()`
    - `mopidy.models.fields.Collection`
    - `mopidy.models.fields.Date`
    - `mopidy.models.fields.Field`
    - `mopidy.models.fields.Identifier`
    - `mopidy.models.fields.Integer`
    - `mopidy.models.fields.String`
    - `mopidy.models.fields.URI`

### Core API

Changes to the Core API affect Mopidy frontends and clients.

#### Import paths

- The [core API](../reference/core.md) is no longer exported from submodules, just from
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
  [`mopidy.types.PlaybackState`][mopidy.types.PlaybackState], where it has been
  unified with `mopidy.audio.PlaybackState`.

#### Root object

- The [`Core`][mopidy.core.Core] class now requires the `config` argument to be
  present. As this argument is provided by Mopidy itself at runtime, this should
  only affect the setup of extension's test suites.

#### Playback controller

- [`PlaybackController.play()`][mopidy.core.PlaybackController.play]
  no longer accepts [`TlTrack`][mopidy.models.TlTrack] objects,
  which has been deprecated since Mopidy 3.0.
  Use tracklist IDs (`tlid`) instead.
  (#1855, !2150)

    There are a few APIs left that still support `TlTrack` objects where a
    simple tracklist ID should be used instead, but these have long been
    deprecated and will be removed in later releases, once our test suites have
    been updated to not rely so heavily on the use of `TlTrack` objects in API
    calls.

### Backend API

Changes to the Backend API affect Mopidy backend extensions.

- Document that [`Backend`][mopidy.backend.Backend] is instantiated with two
  keyword arguments, `config` and `audio`. (!2253)

- Remove the attribute `Backend.audio` from the documentation. Mopidy core does
  not rely on a backend exposing this attribute, and the default backend
  constructor does not set this attribute. How the `config` and `audio`
  arguments are used is up to the backend implementation, but they are provided
  for backends to use if they need them. (!2253)

- Added
  [`LibraryProvider.lookup_many()`][mopidy.backend.LibraryProvider.lookup_many]
  to take a list of URIs and return a mapping of URIs to tracks. If this method
  is not implemented then repeated calls to
  [`LibraryProvider.lookup()`][mopidy.backend.LibraryProvider.lookup] will be
  used as a fallback. (!2145)

- Deprecated
  [`LibraryProvider.lookup()`][mopidy.backend.LibraryProvider.lookup].
  Extensions should implement
  [`LibraryProvider.lookup_many()`][mopidy.backend.LibraryProvider.lookup_many]
  instead. (!2145)

### Audio API

Changes to the Audio API only affect the few Mopidy backend extensions that
interface with the audio layer themselves.

- The audio API is no longer exported from submodules, just from
  [`mopidy.audio`][mopidy.audio]. Update your imports accordingly. The removed
  modules are:

    - `mopidy.audio.actor`
    - `mopidy.audio.listener`
    - `mopidy.audio.utils`

- The old audio actor has been split into a [`Audio`][mopidy.audio.Audio]
  interface with the API used by core and backends, and a
  [`GstAudio`][mopidy.audio.GstAudio] implementation using GStreamer.
  The API is still very specific to GStreamer, but this split makes it a bit
  easier to mock out the audio layer in tests as it is clearer what is part of
  the required interface. (!2224)

- Moved `mopidy.audio.PlaybackState` to
  [`mopidy.types.PlaybackState`][mopidy.types.PlaybackState], where it has been
  unified with `mopidy.core.PlaybackState`.

- The [`convert_tags_to_track()`][mopidy.audio.tags.convert_tags_to_track]
  function now requires the track `uri` as an argument, so that it can construct
  valid [`Track`][mopidy.models.Track] objects.

- Removed APIs only used by Mopidy-Spotify's bespoke audio delivery mechanism,
  which has not been used since Spotify shut down their libspotify APIs in
  May 2022. The removed functions/methods are:

    - `mopidy.audio.Audio.emit_data()`
    - `mopidy.audio.Audio.set_appsrc()`
    - `mopidy.audio.Audio.set_metadata()`
    - `mopidy.audio.calculate_duration()`
    - `mopidy.audio.create_buffer()`
    - `mopidy.audio.millisecond_to_clocktime()`

### Type hints

- Added type hints to most of the source code to make it safer to do changes,
  to catch bugs earlier, and to make it faster to navigate the code base. Pykka
  actor proxies are fully supported, so you should be able to see what type of
  object you get back when you call an actor method, and what type of arguments
  the method expects.

- We now have a public `mopidy.types` module with types that are useful both for
  Mopidy core and extensions. This module will probably see tweaks going
  forward, and should not be considered entirely stable yet. However, if you
  limit your use of this module in your extension to with `if TYPE_CHECKING:`
  code blocks, your extension should continue to work at runtime even if this
  module sees breaking changes.

- Switched from mypy to pyright and ty for type checking. The jury is still out
  on which we'll use long-term. (!2226)

### Private modules

- Moved bundled extensions to the private package `mopidy._exts`. (!2217)

    The removed modules are:

    - `mopidy.file`
    - `mopidy.http`
    - `mopidy.m3u`
    - `mopidy.softwaremixer`
    - `mopidy.stream`

- Renamed modules to be explicitly private. (!2226)

    The removed modules are:

    - `mopidy.config.keyring`
    - `mopidy.internal.*`

### Development process

- We've dropped the split between the `main` and `develop` branches in our
  development process. We now use `main` for all development, and have removed
  the `develop` branch.

- All docstrings have been ported from reStructuredText to Markdown in Google
  style. All docs have been ported from reStructuredText to Markdown, and we now
  use Zensical to build our docs. During the process, there has been quite a bit
  of improvements to the docs, but there are clearly corners that still need
  dusting and updating. (!2247)

- The [`mopidy-ext-template`](https://github.com/mopidy/mopidy-ext-template)
  extension template has been heavily modernized over the last year. All of the
  extensions maintained in the Mopidy GitHub organization have been updated to
  the latest version of the template, and we strongly recommend maintainers of
  other extensions to update their extensions to the latest version of the
  template as well. With the move from cookiecutter to Copier, it is now much
  easier to use the template to update existing extensions, not just create new
  ones.
