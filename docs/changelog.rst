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

- Python >= 3.11 is now required. Python 3.7-3.10 are no longer supported.

- GStreamer >= 1.22.0 is now required.

- msgspec >= 0.18.6 is now required.

- PyGObject >= 3.42 is now an explicit Python dependency, and not something we
  assume you'll install together with GStreamer.

- Pykka >= 4.0 is now required.

- Requests >= 2.28 is now required.

- Setuptools >= 66 is now required.

- Tornado >= 6.2 is now required.

- Replaced :mod:`pkg_resources` with :mod:`importlib.metadata` from Python's
  standard library.

Core API
--------

Changes to the Core API may affect Mopidy clients.

Some of the changes in the Core API are related to replacing the use of
full ``TlTrack`` objects as API arguments with tracklist IDs, ``tlid``.
This is especially relevant for remote clients, like web clients, which may
pass a lot less data over the network when using tracklist IDs in API calls.

Root object
^^^^^^^^^^^

- The :class:`mopidy.core.Core` class now requires the `config` argument to be
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

Models
------

Changes to the data models may affect any Mopidy extension or client.

- Our models are now based on the `msgspec <https://jcristharif.com/msgspec/>`_
  library, which means that they are now fully typed. Memory usage should be
  similar, but JSON encodding/decoding a lot faster. This change might cause
  issues in extensions that have not been tested and updated to work with Mopidy
  4.0.

Audio API
---------

Changes to the Audio API may affect a few Mopidy backend extensions.

- Removed APIs only used by Mopidy-Spotify's bespoke audio delivery mechanism,
  which has not been used since Spotify shut down their libspotify APIs in
  May 2022. The removed functions/methods are:

  - :meth:`mopidy.audio.Audio.emit_data`
  - :meth:`mopidy.audio.Audio.set_appsrc`
  - :meth:`mopidy.audio.Audio.set_metadata`
  - :func:`mopidy.audio.calculate_duration`
  - :func:`mopidy.audio.create_buffer`
  - :func:`mopidy.audio.millisecond_to_clocktime`

Extension support
-----------------

- The command :command:`mopidy deps` no longer repeats transitive dependencies
  that have already been listed. This reduces the length of the command's output
  drastically. (PR: :issue:`2152`)

Internals
---------

- Dropped split between the ``main`` and ``develop`` branches. We now use
  ``main`` for all development, and have removed the ``develop`` branch.

- Added type hints to most of the source code.

- Switched from mypy to pyright for type checking.


v3.4.2 (2023-11-01)
===================

- Deps: Python 3.11 and 3.12 are now included in the testing matrix.

- M3U: Stop following symlinks when :confval:`file/follow_symlinks` is false.
  (PR: :issue:`2094`)

- zeroconf: Fix exception on shutdown if `dbus` is not installed.

- Docs: Fix crash when building docs on recent Sphinx versions.

- Dev: Make stacktraces from deprecation warnings include the offending call
  site, to help upgrade API usage in extensions.

- Dev: Upgrade CI workflows to fix Node.js 12 deprecation notices and avoid
  Codecov's bash uploader.

- Dev: Make tests pass on macOS. (PR: :issue:`2092`)

- Dev: Incease test coverage of Mopidy-File to 100%. (PR: :issue:`2096`)

- Dev: Added ``"tox -e ci``", to allow easy CI check before ``git push``.


v3.4.1 (2022-12-07)
===================

- HTTP: Fix non-optional :confval:`http/allowed_origins` config setting. (PR:
  :issue:`2066`)


v3.4.0 (2022-11-28)
===================

- Config: Handle DBus "Algorithm plain is not supported" error. (PR: :issue:`2061`)

- File: Fix uppercase :confval:`file/excluded_file_extensions`. (PR:
  :issue:`2063`)

- Add :meth:`mopidy.backend.PlaybackProvider.on_source_setup` which can be
  implemented by Backend playback providers that want to set GStreamer source
  properties in the ``source-setup`` callback. (PR: :issue:`2060`)

- HTTP: Improve handling of :confval:`http/allowed_origins` config setting. (PR: :issue:`2054`)


v3.3.0 (2022-04-29)
===================

- Core: Fixes invalid verbosity logging levels. (Fixes: :issue:`1947`,
  PR: :issue:`2021`)

- Core: Fix TypeError exception when playing track with unnamed artists.
  (Fixes: :issue:`1991`, PR: :issue:`2012`)

- Core: Fix startup crash when loading invalid extensions. (PR:
  :issue:`1990`)

- Core: Fix error-handling when fetching backend support info. (PR:
  :issue:`1964`)

- Core: Align values supported by the ``field`` argument to
  :meth:`mopidy.core.LibraryController.get_distinct` with Mopidy search query
  fields, with the exception of 'any'. Deprecated field 'track' with the
  goal of removing it in the next major release, use 'track_name' instead.
  Backends should support both `track` and `track_name` until they require
  a version of Mopidy where `track` has been removed.
  (Fixes: :issue:`1900`, PR: :issue:`1899`)

- Core: Add ``musicbrainz_albumid``, ``musicbrainz_artistid``,
  ``musicbrainz_trackid``, and ``disc_no`` to the permitted search query
  fields. (Fixes: :issue:`1900`, PR: :issue:`1899`)

- Audio: Fix TypeError when handling create output pipeline errors.
  (Fixes: :issue:`1924`, PR: :issue:`2040`)

- Audio: Fix seek when stopped. (Fixes: :issue:`2005`, PR: :issue:`2006`)

- Config: Fix support for inline comments, a regression introduced during
  our Python 3 migration. (Fixes: :issue:`1868`, PR: :issue:`2041`)

- HTTP: Fix missing CORS headers on RPC response. (Fixes: :issue:`2028`,
  PR: :issue:`2029`)

- HTTP: Improve CSRF protection Content-Type check. (PR: :issue:`1997`)

- HTTP: Fix support for websocket clients connecting/disconnecting
  during broadcast. (PR: :issue:`1993`)

- Add Python 3.10 to our test matrix.

- Core: Added and improved configuration parsing code for extension
  developers. (PR: :issue:`2010`)


v3.2.0 (2021-07-08)
===================

- Initial type annotations and mypy support. (PR: :issue:`1842`)

- Move CI to GitHub Actions (PR: :issue:`1951`)

- Fix logging during extension loading (Fixes: :issue:`1958`, PR:
  :issue:`1960`)

- Fix appsrc track change after live-mode previously set. (Fixes:
  :issue:`1969`, PR: :issue:`1971`)


v3.1.1 (2020-12-26)
===================

- Fix crash when extracting tags using gst-python >= 1.18. (PR:
  :issue:`1948`)


v3.1.0 (2020-12-16)
===================

- Add Python 3.9 to our test matrix.

- Add :meth:`mopidy.backend.PlaybackProvider.should_download` which can be
  implemented by playback providers that want to use GStreamer's download
  buffering strategy for their URIs. (PR: :issue:`1888`)

- Audio: Fix memory leak when converting GStreamer ``sample`` type tags.
  (Fixes: :issue:`1827`, PR: :issue:`1929`)

- Turn off strict parsing of ``*.pls`` playlist files. This was a regression
  that happened during the migration to Python 3. (PR: :issue:`1923`)

- Make the systemd unit that ships with Mopidy wait for an Internet
  connection before starting Mopidy. When used by distribution packages, this
  can help avoid that extensions try to connect to cloud services before the
  machine's Internet connection is ready for use. (PR: :issue:`1946`)


v3.0.2 (2020-04-02)
===================

Bugfix release.

- Core: Reset stream title on receipt of any ``title`` audio tag change.
  (Fixes: :issue:`1871`, PR: :issue:`1875`)

- Core: Hide the methods :meth:`mopidy.core.Core.setup` and
  :meth:`mopidy.core.Core.teardown` from other actors and JSON-RPC API
  clients. The methods have always been clearly documented as internal. (PR:
  :issue:`1865`)

- Config: Log a warning if unknown config sections are found. (Fixes:
  :issue:`1878`, PR: :issue:`1890`)

- Config: Fix crash when reading values from keyring. (PR: :issue:`1887`)

- Various documentation updates.


v3.0.1 (2019-12-22)
===================

Bugfix release.

- Remove :mod:`mopidy.local` migration helper. (Fixes: :issue:`1861`, PR: :issue:`1862`)


v3.0.0 (2019-12-22)
===================

The long-awaited Mopidy 3.0 is finally here, just in time for the Mopidy
project's 10th anniversary on December 23rd!

Mopidy 3.0 is a backward-incompatible release in a pretty significant way:
Mopidy no longer runs on Python 2.

**Mopidy 3.0 requires Python 3.7 or newer.**

While extensions have been able to continue working without changes
throughout the 1.x and 2.x series of Mopidy, this time is different:

- All extensions must be updated to work on Python 3.7 and newer.

- Some extensions need to replace their use of a few long-deprecated APIs
  that we've removed. See below for details.

- Extension maintainers are also encouraged to update their project's setup to
  match our refreshed `extension cookiecutter`_.

In parallel with the development of Mopidy 3.0, we've coordinated with a few
extension maintainers and upgraded almost 20 of the most popular extensions.
These will all be published shortly after the release of Mopidy 3.0.

We've also built a new `extension registry`_, where you can quickly track what
extensions are ready for Python 3.

In other news, the `Mopidy-MPD`_ and `Mopidy-Local`_ extensions have grown up
and moved out to flourish as independent extension projects.
After the move, Mopidy-Local merged with Mopidy-Local-SQLite and
Mopidy-Local-Images, which are now both a part of the Mopidy-Local extension.

.. _extension cookiecutter: https://github.com/mopidy/cookiecutter-mopidy-ext
.. _extension registry: https://mopidy.com/ext/
.. _Mopidy-MPD: https://mopidy.com/ext/mpd/
.. _Mopidy-Local: https://mopidy.com/ext/local/


Dependencies
------------

- Python >= 3.7 is now required. Python 2.7 is no longer supported.

- GStreamer >= 1.14.0 is now required.

- Pykka >= 2.0.1 is now required.

- Tornado >= 4.4 is now required. The upper boundary (< 6) has been removed.

- We now use a number of constants and functions from ``GLib`` instead of their
  deprecated equivalents in ``GObject``. The exact version of PyGObject and
  GLib that makes these constants and functions available in the new location
  is not known, but is believed to have been released in 2015 or earlier.

Logging
-------

- The command line option ``mopidy --save-debug-log`` and the
  configuration :confval:`logging/debug_file` have been removed.
  To save a debug log for sharing, run ``mopidy -vvvv 2>&1 | tee mopidy.log``
  or equivalent. (Fixes: :issue:`1452`, PR: :issue:`1783`)

- Replaced the configurations :confval:`logging/console_format`
  and :confval:`logging/debug_format` with
  the single configuration :confval:`logging/format`.
  It defaults to the same format as the old debug format.
  (Fixes: :issue:`1452`, PR: :issue:`1783`)

- Added configuration :confval:`logging/verbosity` to be able to control
  logging verbosity from the configuration file,
  in addition to passing ``-q`` or ``-v`` on the command line.
  (Fixes: :issue:`1452`, PR: :issue:`1783`)

Core API
--------

- Removed properties, methods, and arguments that have been deprecated since
  1.0, released in 2015.
  Everything removed already has a replacement, that should be used instead.
  See below for a full list of removals and replacements.
  (Fixes: :issue:`1083`, :issue:`1461`, PR: :issue:`1768`, :issue:`1769`)

Root object
^^^^^^^^^^^

- Removed properties, use getter/setter instead:

  - :attr:`mopidy.core.Core.uri_schemes`
  - :attr:`mopidy.core.Core.version`

Library controller
^^^^^^^^^^^^^^^^^^

- Removed methods:

  - :meth:`mopidy.core.LibraryController.find_exact`:
    Use :meth:`~mopidy.core.LibraryController.search`
    with the keyword argument ``exact=True`` instead.

- Removed the ``uri`` argument to
  :meth:`mopidy.core.LibraryController.lookup`.
  Use the ``uris`` argument instead.

- Removed the support for passing the search query as keyword arguments to
  :meth:`mopidy.core.LibraryController.search`.
  Use the ``query`` argument instead.

- :meth:`mopidy.core.LibraryController.search` now returns an empty result
  if there is no ``query``. Previously, it returned the full music library.
  This is not feasible for online music services and has thus been deprecated
  since 1.0.

Playback controller
^^^^^^^^^^^^^^^^^^^

- Removed properties, use getter/setter instead:

  - :attr:`mopidy.core.PlaybackController.current_tl_track`
  - :attr:`mopidy.core.PlaybackController.current_track`
  - :attr:`mopidy.core.PlaybackController.state`
  - :attr:`mopidy.core.PlaybackController.time_position`

- Moved to the mixer controller:

  - :meth:`mopidy.core.PlaybackController.get_mute`:
    Use :meth:`~mopidy.core.MixerController.get_mute`.

  - :meth:`mopidy.core.PlaybackController.get_volume`:
    Use :meth:`~mopidy.core.MixerController.get_volume`.

  - :meth:`mopidy.core.PlaybackController.set_mute`:
    Use :meth:`~mopidy.core.MixerController.set_mute`.

  - :meth:`mopidy.core.PlaybackController.set_volume`:
    Use :meth:`~mopidy.core.MixerController.set_volume`.

  - :attr:`mopidy.core.PlaybackController.mute`:
    Use :meth:`~mopidy.core.MixerController.get_mute`
    and :meth:`~mopidy.core.MixerController.set_mute`.

  - :attr:`mopidy.core.PlaybackController.volume`:
    Use :meth:`~mopidy.core.MixerController.get_volume`
    and :meth:`~mopidy.core.MixerController.set_volume`.

- Deprecated the ``tl_track`` argument to
  :meth:`mopidy.core.PlaybackController.play`, with the goal of removing it in
  the next major release. Use the ``tlid`` argument instead.
  (Fixes: :issue:`1773`, PR: :issue:`1786`, :issue:`1854`)

Playlist controller
^^^^^^^^^^^^^^^^^^^

- Removed properties, use getter/setter instead:

  - :attr:`mopidy.core.PlaylistController.playlists`

- Removed methods:

  - :meth:`mopidy.core.PlaylistsController.filter`:
    Use :meth:`~mopidy.core.PlaylistsController.as_list` and filter yourself.

  - :meth:`mopidy.core.PlaylistsController.get_playlists`:
    Use :meth:`~mopidy.core.PlaylistsController.as_list` and
    :meth:`~mopidy.core.PlaylistsController.get_items`.

Tracklist controller
^^^^^^^^^^^^^^^^^^^^

- Removed properties, use getter/setter instead:

  - :attr:`mopidy.core.TracklistController.tl_tracks`
  - :attr:`mopidy.core.TracklistController.tracks`
  - :attr:`mopidy.core.TracklistController.length`
  - :attr:`mopidy.core.TracklistController.version`
  - :attr:`mopidy.core.TracklistController.consume`
  - :attr:`mopidy.core.TracklistController.random`
  - :attr:`mopidy.core.TracklistController.repeat`
  - :attr:`mopidy.core.TracklistController.single`

- Removed the ``uri`` argument to
  :meth:`mopidy.core.TracklistController.add`.
  Use the ``uris`` argument instead.

- Removed the support for passing filter criteria as keyword arguments to
  :meth:`mopidy.core.TracklistController.filter`.
  Use the ``criteria`` argument instead.

- Removed the support for passing filter criteria as keyword arguments to
  :meth:`mopidy.core.TracklistController.remove`.
  Use the ``criteria`` argument instead.

- Deprecated methods, with the goal of removing them in the next major release:
  (Fixes: :issue:`1773`, PR: :issue:`1786`, :issue:`1854`)

  - :meth:`mopidy.core.TracklistController.eot_track`.
    Use :meth:`~mopidy.core.TracklistController.get_eot_tlid` instead.

  - :meth:`mopidy.core.TracklistController.next_track`.
    Use :meth:`~mopidy.core.TracklistController.get_next_tlid` instead.

  - :meth:`mopidy.core.TracklistController.previous_track`.
    Use :meth:`~mopidy.core.TracklistController.get_previous_tlid` instead.

- The ``tracks`` argument to :meth:`mopidy.core.TracklistController.add` has
  been deprecated since Mopidy 1.0. It is still deprecated, with the goal of
  removing it in the next major release. Use the ``uris`` argument instead.

Backend API
-----------

- Add :meth:`mopidy.backend.PlaybackProvider.is_live` which can be
  implemented by playback providers that want to mark their URIs as
  live streams that should not be buffered. (PR: :issue:`1845`)

Models
------

- Remove ``.copy()`` method on all model classes.
  Use the ``.replace()`` method instead.
  (Fixes: :issue:`1464`, PR: :issue:`1774`)

- Remove :attr:`mopidy.models.Album.images`.
  Clients should use :meth:`mopidy.core.LibraryController.get_images` instead.
  Backends should implement :meth:`mopidy.backend.LibraryProvider.get_images`.
  (Fixes: :issue:`1464`, PR: :issue:`1774`)

Extension support
-----------------

- The following methods now return :class:`pathlib.Path` objects instead
  of strings:

  - :meth:`mopidy.ext.Extension.get_cache_dir`
  - :meth:`mopidy.ext.Extension.get_config_dir`
  - :meth:`mopidy.ext.Extension.get_data_dir`

  This makes it easier to support arbitrary encoding in file names.

- The command :command:`mopidy deps` no longer repeats the dependencies of
  Mopidy itself for every installed extension. This reduces the length of the
  command's output drastically. (PR: :issue:`1846`)

HTTP frontend
-------------

- Stop bundling Mopidy.js and serving it at ``/mopidy/mopidy.js`` and
  ``/mopidy/mopidy.min.js``. All Mopidy web clients must use Mopidy.js from npm
  or vendor their own copy of the library.
  (Fixes: :issue:`1083`, :issue:`1460`, PR: :issue:`1708`)

- Remove support for serving arbitrary files over HTTP through the use of
  :confval:`http/static_dir`, which has been deprecated since 1.0. (Fixes:
  :issue:`1463`, PR: :issue:`1706`)

- Add option :confval:`http/default_app` to redirect from web server root
  to a specific app instead of Mopidy's web app list. (PR: :issue:`1791`)

- Add cookie secret to Tornado web server, allowing Tornado request handlers to
  call ``get_secure_cookie()``, in an implementation of ``get_current_user()``.
  (PR: :issue:`1801`)

MPD frontend
------------

- The Mopidy-MPD frontend is no longer bundled with Mopidy, and has been moved
  to its own `Git repo <https://github.com/mopidy/mopidy-mpd>`__ and
  `PyPI project <https://pypi.org/project/Mopidy-MPD>`__.

Local backend
-------------

- The Mopidy-Local backend is no longer bundled with Mopidy, and has been moved
  to its own `Git repo <https://github.com/mopidy/mopidy-local>`__ and
  `PyPI project <https://pypi.org/project/Mopidy-Local>`__.
  (Fixes: :issue:`1003`)

- Removed :exc:`mopidy.exceptions.FindError`, as it was only used by
  Mopidy-Local. (PR: :issue:`1857`)

Audio
-----

- Remove the method :meth:`mopidy.audio.Audio.emit_end_of_stream`, which has
  been deprecated since 1.0. (Fixes: :issue:`1465`, PR: :issue:`1705`)

- Add ``live_stream`` option to :meth:`mopidy.audio.Audio.set_uri`
  that disables buffering, which reduces latency before playback starts,
  and discards data when paused. (PR: :issue:`1845`)

Internals
---------

- Format code with Black. (PR: :issue:`1834`)

- Port test assertions from ``unittest`` methods to pytest ``assert``
  statements. (PR: :issue:`1838`)

- Switch all internal path handling to use :mod:`pathlib`. (Fixes:
  :issue:`1744`, PR: :issue:`1814`)

- Remove :mod:`mopidy.compat` and all Python 2/3 compatibility code. (PR:
  :issue:`1833`, :issue:`1835`)

- Replace ``requirements.txt`` and ``setup.py`` with declarative config in
  ``setup.cfg``. (PR: :issue:`1839`)

- Refreshed and updated all of our end user-oriented documentation.
