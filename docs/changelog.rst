.. _changelog:

*********
Changelog
*********

This changelog is used to track all major changes to Mopidy.

For older releases, see :ref:`history`.


v4.0.0 (UNRELEASED)
===================

Mopidy 4.0 is a backward-incompatible release because we've dropped support for
old versions of our dependencies and a number of deprecated APIs.

Dependencies
------------

In general, we require the version of each dependency that is available in
the latest Debian stable release, Debian 13 Trixie.

- Python >= 3.13 is now required.
  Support for 3.7-3.12 has been dropped,
  while Python 3.13-3.14 has been added to the testing matrix.

- Replaced :mod:`pkg_resources` with :mod:`importlib.metadata` from Python's
  standard library, removing the runtime dependency on setuptools.

- GStreamer >= 1.26.2 is now required.

- PyGObject >= 3.50 is now an explicit Python dependency. Previously we assumed
  that you would install this together with your GStreamer installation.

- Pykka >= 4.1 is now required.

- Pydantic >= 2.10 is now required. This is a new dependency for Mopidy to
  replace our custom data models.

- Cyclopts >= 3.12 is now required. This is a new dependency for Mopidy to build
  the command line interfaces, replacing our use of :mod:`argparse`.

- Requests >= 2.32 is now required.

- Tornado >= 6.4 is now required.

Data models
-----------

Changes to the data models may affect any Mopidy extension or client.

- The ``Track`` and ``Playlist`` models now requires the ``uri`` field to always
  be set. (Fixes: :issue:`2190`, PR: :issue:`2229`)

- The models are now based on Pydantic data classes, which means:

  - All models fields and the ``replace()`` method should work as before, so
    unless your extension modifies or adds models, this should not affect you.

  - Models are now type-checked at runtime. This should help catch bugs early.

- Since we now use Pydantic to convert data models to and from JSON, the old
  model machinery has been removed. This includes the following:

  - :class:`mopidy.models.ImmutableObject` -- Not used by Mopidy since v1.0.5
    ten years ago.
  - :class:`mopidy.models.ValidatedImmutableObject` -- The old base class for
    all models.
  - :class:`mopidy.models.ModelJSONEncoder`
  - :func:`mopidy.models.model_json_decoder`
  - :class:`mopidy.models.fields.Collection`
  - :class:`mopidy.models.fields.Date`
  - :class:`mopidy.models.fields.Field`
  - :class:`mopidy.models.fields.Identifier`
  - :class:`mopidy.models.fields.Integer`
  - :class:`mopidy.models.fields.String`
  - :class:`mopidy.models.fields.URI`

Core API
--------

Changes to the Core API may affect Mopidy clients.

Some of the changes in the Core API are related to replacing the use of
full ``TlTrack`` objects as API arguments with tracklist IDs, ``tlid``.
This is especially relevant for remote clients, like web clients, which may
pass a lot less data over the network when using tracklist IDs in API calls.

- The core API is no longer exported from submodules, just from
  :mod:`mopidy.core`. Update your imports accordingly. The removed modules are:

  - :mod:`mopidy.core.actor`
  - :mod:`mopidy.core.history`
  - :mod:`mopidy.core.library`
  - :mod:`mopidy.core.listener`
  - :mod:`mopidy.core.mixer`
  - :mod:`mopidy.core.playback`
  - :mod:`mopidy.core.playlists`
  - :mod:`mopidy.core.tracklist`

- Moved :class:`mopidy.core.PlaybackState` to
  :class:`mopidy.types.PlaybackState`.

Root object
^^^^^^^^^^^

- The :class:`mopidy.core.Core` class now requires the ``config`` argument to be
  present. As this argument is provided by Mopidy itself at runtime, this
  should only affect the setup of extension's test suites.

Library controller
^^^^^^^^^^^^^^^^^^

- No changes so far.

Playback controller
^^^^^^^^^^^^^^^^^^^

- :meth:`mopidy.core.PlaybackController.play`
  no longer accepts ``TlTrack`` objects,
  which has been deprecated since Mopidy 3.0.
  Use tracklist IDs (``tlid``) instead.
  (Fixes :issue:`1855`, PR: :issue:`2150`)

Playlist controller
^^^^^^^^^^^^^^^^^^^

- No changes so far.

Tracklist controller
^^^^^^^^^^^^^^^^^^^^

- No changes so far.

Backend API
-----------

Changes to the Backend API may affect Mopidy backend extensions.

- Added :meth:`mopidy.backend.LibraryProvider.lookup_many` to take a list of
  URIs and return a mapping of URIs to tracks. If this method is not implemented
  then repeated calls to :meth:`mopidy.backend.LibraryProvider.lookup` will be
  used as a fallback.

- Deprecated :meth:`mopidy.backend.LibraryProvider.lookup`. Extensions should
  implement :meth:`mopidy.backend.LibraryProvider.lookup_many` instead.


Audio API
---------

Changes to the Audio API may affect a few Mopidy backend extensions.

- The old audio actor has been split into a :class:`mopidy.audio.Audio`
  interface with the API used by core and backends, and a
  :class:`mopidy.audio.GstAudio` implementation using GStreamer.
  The API is still very specific to GStreamer, but this split makes it a bit
  easier to mock out the audio layer in tests.

- The audio API is no longer exported from submodules, just from
  :mod:`mopidy.audio`. Update your imports accordingly. The removed modules are:

  - :mod:`mopidy.audio.actor`
  - :mod:`mopidy.audio.listener`
  - :mod:`mopidy.audio.utils`

- Moved :class:`mopidy.audio.PlaybackState` to
  :class:`mopidy.types.PlaybackState`.

- The :func:`mopidy.audio.tags.convert_tags_to_track` function now requires the
  track ``uri`` as an argument, so that it can construct valid
  :class:`~mopidy.models.Track` objects.

- Removed APIs only used by Mopidy-Spotify's bespoke audio delivery mechanism,
  which has not been used since Spotify shut down their libspotify APIs in
  May 2022. The removed functions/methods are:

  - :meth:`mopidy.audio.Audio.emit_data`
  - :meth:`mopidy.audio.Audio.set_appsrc`
  - :meth:`mopidy.audio.Audio.set_metadata`
  - :func:`mopidy.audio.calculate_duration`
  - :func:`mopidy.audio.create_buffer`
  - :func:`mopidy.audio.millisecond_to_clocktime`

Extension API
-------------

- Breaking change for extensions with their own CLI commands:

  The :mod:`mopidy.commands` module which extended on :mod:`argparse` to let
  extensions add their own CLI subcommands has been removed. We now use new
  dependency Cyclopts to build command line interfaces. The extensions
  maintained by the core team, including ``mopidy-local`` and
  ``mopidy-spotify``, has been updated to use Cyclopts. The migration is pretty
  straight forward, but feel free to reach out for help with migrating your
  extension. (PR: :issue:`2234`)

Extension support
-----------------

- The command :command:`mopidy deps` no longer repeats transitive dependencies
  that have already been listed. This reduces the length of the command's output
  drastically. (PR: :issue:`2152`)

Audio
-----

- Workaround GStreamer ``Gst.Structure().get_name()`` regression for versions
  v1.26.0 to v1.26.2 (inclusive). (PR: :issue:`2094`)

Internals
---------

- Dropped split between the ``main`` and ``develop`` branches. We now use
  ``main`` for all development, and have removed the ``develop`` branch.

- Added type hints to most of the source code.

- Switched from mypy to pyright and ty for type checking. The jury is still out
  on which we'll use long-term.

- Moved bundled extensions to the private package :mod:`mopidy._exts`. The
  removed modules are:

  - :mod:`mopidy.file`
  - :mod:`mopidy.http`
  - :mod:`mopidy.m3u`
  - :mod:`mopidy.softwaremixer`
  - :mod:`mopidy.stream`

- Renamed modules to be explicitly private:

  - :mod:`mopidy.config.keyring`
  - :mod:`mopidy.internal.*`
