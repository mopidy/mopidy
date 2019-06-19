********************
Changelog 1.x series
********************

This is the changelog of Mopidy v1.0.0 through v1.1.2.

For the latest releases, see :ref:`changelog`.


v1.1.2 (2016-01-18)
===================

Bug fix release.

- Main: Catch errors when loading the :confval:`logging/config_file` file.
  (Fixes: :issue:`1320`)

- Core: If changing to another track while the player is paused, the new track
  would not be added to the history or marked as currently playing. (Fixes:
  :issue:`1352`, PR: :issue:`1356`)

- Core: Skips over unplayable tracks if the user attempts to change tracks
  while paused, like we already did if in playing state. (Fixes :issue:`1378`,
  PR: :issue:`1379`)

- Core: Make :meth:`~mopidy.core.LibraryController.lookup` ignore tracks with
  empty URIs. (Partly fixes: :issue:`1340`, PR: :issue:`1381`)

- Core: Fix crash if backends emits events with wrong names or arguments.
  (Fixes: :issue:`1383`)

- Stream: If an URI is considered playable, don't consider it as a candidate
  for playlist parsing. Just looking at MIME type prefixes isn't enough, as for
  example Ogg Vorbis has the MIME type ``application/ogg``. (Fixes:
  :issue:`1299`)

- Local: If the scan or clear commands are used on a library that does not
  exist, exit with an error. (Fixes: :issue:`1298`)

- MPD: Notify idling clients when a seek is performed. (Fixes: :issue:`1331`)

- MPD: Don't return tracks with empty URIs. (Partly fixes: :issue:`1340`, PR:
  :issue:`1343`)

- MPD: Add ``volume`` command that was reintroduced, though still as a
  deprecated command, in MPD 0.18 and is in use by some clients like mpc.
  (Fixes: :issue:`1393`, PR: :issue:`1397`)

- Proxy: Handle case where :confval:`proxy/port` is either missing from config
  or set to an empty string. (PR: :issue:`1371`)


v1.1.1 (2015-09-14)
===================

Bug fix release.

- Dependencies: Specify that we need Requests >= 2.0, not just any version.
  This ensures that we fail earlier if Mopidy is used with a too old Requests.

- Core: Make :meth:`mopidy.core.LibraryController.refresh` work for all
  backends with a library provider. Previously, it wrongly worked for all
  backends with a playlists provider. (Fixes: :issue:`1257`)

- Core: Respect :confval:`core/cache_dir` and :confval:`core/data_dir` config
  values added in 1.1.0 when creating the dirs Mopidy need to store data. This
  should not change the behavior for desktop users running Mopidy. When running
  Mopidy as a system service installed from a package which sets the core dir
  configs properly (e.g. Debian and Arch packages), this fix avoids the
  creation of a couple of directories that should not be used, typically
  :file:`/var/lib/mopidy/.local` and :file:`/var/lib/mopidy/.cache`. (Fixes:
  :issue:`1259`, PR: :issue:`1266`)

- Core: Fix error in :meth:`~mopidy.core.TracklistController.get_eot_tlid`
  docstring. (Fixes: :issue:`1269`)

- Audio: Add ``timeout`` parameter to :meth:`~mopidy.audio.scan.Scanner.scan`.
  (Part of: :issue:`1250`, PR: :issue:`1281`)

- Extension support: Make :meth:`~mopidy.ext.Extension.get_cache_dir`,
  :meth:`~mopidy.ext.Extension.get_config_dir`, and
  :meth:`~mopidy.ext.Extension.get_data_dir` class methods, so they can be used
  without creating an instance of the :class:`~mopidy.ext.Extension` class.
  (Fixes: :issue:`1275`)

- Local: Deprecate :confval:`local/data_dir` and respect
  :confval:`core/data_dir` instead. This does not change the defaults for
  desktop users, only system services installed from packages that properly set
  :confval:`core/data_dir`, like the Debian and Arch packages. (Fixes:
  :issue:`1259`, PR: :issue:`1266`)

- Local: Change default value of :confval:`local/scan_flush_threshold` from
  1000 to 100 to shorten the time Mopidy-Local-SQLite blocks incoming requests
  while scanning the local library.

- M3U: Changed default for the :confval:`m3u/playlists_dir` from
  ``$XDG_DATA_DIR/mopidy/m3u`` to unset, which now means the extension's data
  dir. This does not change the defaults for desktop users, only system
  services installed from packages that properly set :confval:`core/data_dir`,
  like the Debian and Arch pakages. (Fixes: :issue:`1259`, PR: :issue:`1266`)

- Stream: Expand nested playlists to find the stream URI. This used to work,
  but regressed in 1.1.0 with the extraction of stream playlist parsing from
  GStreamer to being handled by the Mopidy-Stream backend. (Fixes:
  :issue:`1250`, PR: :issue:`1281`)

- Stream: If "file" is present in the :confval:`stream/protocols` config value
  and the :ref:`ext-file` extension is enabled, we exited with an error because
  two extensions claimed the same URI scheme. We now log a warning recommending
  to remove "file" from the :confval:`stream/protocols` config, and then
  proceed startup. (Fixes: :issue:`1248`, PR: :issue:`1254`)

- Stream: Fix bug in new playlist parser. A non-ASCII char in an urilist
  comment would cause a crash while parsing due to comparison of a non-ASCII
  bytestring with a Unicode string. (Fixes: :issue:`1265`)

- File: Adjust log levels when failing to expand ``$XDG_MUSIC_DIR`` into a real
  path. This usually happens when running Mopidy as a system service, and thus
  with a limited set of environment variables. (Fixes: :issue:`1249`, PR:
  :issue:`1255`)

- File: When browsing files, we no longer scan the files to check if they're
  playable. This makes browsing of the file hierarchy instant for HTTP clients,
  which do no scanning of the files' metadata, and a bit faster for MPD
  clients, which no longer scan the files twice. (Fixes: :issue:`1260`, PR:
  :issue:`1261`)

- File: Allow looking up metadata about any ``file://`` URI, just like we did
  in Mopidy 1.0.x, where Mopidy-Stream handled ``file://`` URIs. In Mopidy
  1.1.0, Mopidy-File did not allow one to lookup files outside the directories
  listed in :confval:`file/media_dir`. This broke Mopidy-Local-SQLite when the
  :confval:`local/media_dir` directory was not within one of the
  :confval:`file/media_dirs` directories. For browsing of files, we still limit
  access to files inside the :confval:`file/media_dir` directories. For lookup,
  you can now read metadata for any file you know the path of. (Fixes:
  :issue:`1268`, PR: :issue:`1273`)

- Audio: Fix timeout handling in scanner. This regression caused timeouts to
  expire before it should, causing scans to fail.

- Audio: Update scanner to emit MIME type instead of an error when missing a
  plugin.


v1.1.0 (2015-08-09)
===================

Mopidy 1.1 is here!

Since the release of 1.0, we've closed or merged approximately 65 issues and
pull requests through about 400 commits by a record high 20 extraordinary
people, including 14 newcomers. That's less issues and commits than in the 1.0
release, but even more contributors, and a doubling of the number of newcomers.
Thanks to :ref:`everyone <authors>` who has :ref:`contributed <contributing>`,
especially those that joined the sprint at EuroPython 2015 in Bilbao, Spain a
couple of weeks ago!

As we promised with the release of Mopidy 1.0, any extension working with
Mopidy 1.0 should continue working with all Mopidy 1.x releases. However, this
release brings a lot stronger enforcement of our documented APIs. If an
extension doesn't use the APIs properly, it may no longer work. The advantage
of this change is that Mopidy is now more robust against errors in extensions,
and also provides vastly better error messages when extensions misbehave. This
should make it easier to create quality extensions.

The major features of Mopidy 1.1 are:

- Validation of the arguments to all core API methods, as well as all responses
  from backends and all data model attributes.

- New bundled backend, Mopidy-File. It is similar to Mopidy-Local, but allows
  you to browse and play music from local disk without running a scan to index
  the music first. The drawback is that it doesn't support searching.

- The Mopidy-MPD server should now be up to date with the 0.19 version of the
  MPD protocol.

Dependencies
------------

- Mopidy now requires Requests.

- Heads up: Porting from GStreamer 0.10 to 1.x and support for running Mopidy
  with Python 3.4+ is not far off on our roadmap.

Core API
--------

- **Deprecated:** Calling the following methods with ``kwargs`` is being
  deprecated. (PR: :issue:`1090`)

  - :meth:`mopidy.core.LibraryController.search`
  - :meth:`mopidy.core.PlaylistsController.filter`
  - :meth:`mopidy.core.TracklistController.filter`
  - :meth:`mopidy.core.TracklistController.remove`

- Updated core controllers to handle backend exceptions in all calls that rely
  on multiple backends. (Issue: :issue:`667`)

- Update core methods to do strict input checking. (Fixes: :issue:`700`)

- Add ``tlid`` alternatives to methods that take ``tl_track`` and also add
  ``get_{eot,next,previous}_tlid`` methods as light weight alternatives to the
  ``tl_track`` versions of the calls. (Fixes: :issue:`1131`, PR: :issue:`1136`,
  :issue:`1140`)

- Add :meth:`mopidy.core.PlaybackController.get_current_tlid`.
  (Part of: :issue:`1137`)

- Update core to handle backend crashes and bad data. (Fixes: :issue:`1161`)

- Add :confval:`core/max_tracklist_length` config and limitation. (Fixes:
  :issue:`997` PR: :issue:`1225`)

- Added ``playlist_deleted`` event. (Fixes: :issue:`996`)

Models
------

- Added type checks and other sanity checks to model construction and
  serialization. (Fixes: :issue:`865`)

- Memory usage for models has been greatly improved. We now have a lower
  overhead per instance by using slots, interned identifiers and automatically
  reuse instances. For the test data set this was developed against, a library
  of ~14.000 tracks, went from needing ~75MB to ~17MB. (Fixes: :issue:`348`)

- Added :attr:`mopidy.models.Artist.sortname` field that is mapped to
  ``musicbrainz-sortname`` tag. (Fixes: :issue:`940`)

Configuration
-------------

- Add new configurations to set base directories to be used by Mopidy and
  Mopidy extensions: :confval:`core/cache_dir`, :confval:`core/config_dir`, and
  :confval:`core/data_dir`. (Fixes: :issue:`843`, PR: :issue:`1232`)

Extension support
-----------------

- Add new methods to :class:`~mopidy.ext.Extension` class for getting cache,
  config and data directories specific to your extension:

  - :meth:`mopidy.ext.Extension.get_cache_dir`
  - :meth:`mopidy.ext.Extension.get_config_dir`
  - :meth:`mopidy.ext.Extension.get_data_dir`

  Extensions should use these methods so that the correct directories are used
  both when Mopidy is run by a regular user and when run as a system service.
  (Fixes: :issue:`843`, PR: :issue:`1232`)

- Add :func:`mopidy.httpclient.format_proxy` and
  :func:`mopidy.httpclient.format_user_agent`. (Part of: :issue:`1156`)

- It is now possible to import :mod:`mopidy.backends` without having GObject or
  GStreamer installed. In other words, a lot of backend extensions should now
  be able to run tests in a virtualenv with global site-packages disabled. This
  removes a lot of potential error sources. (Fixes: :issue:`1068`, PR:
  :issue:`1115`)

Local backend
-------------

- Filter out :class:`None` from
  :meth:`~mopidy.backend.LibraryProvider.get_distinct` results. All returned
  results should be strings. (Fixes: :issue:`1202`)

Stream backend
--------------

- Move stream playlist parsing from GStreamer to the stream backend. (Fixes:
  :issue:`671`)

File backend
------------

The :ref:`Mopidy-File <ext-file>` backend is a new bundled backend. It is
similar to Mopidy-Local since it works with local files, but it differs in a
few key ways:

- Mopidy-File lets you browse your media files by their file hierarchy.

- It supports multiple media directories, all exposed under the "Files"
  directory when you browse your library with e.g. an MPD client.

- There is no index of the media files, like the JSON or SQLite files used by
  Mopidy-Local. Thus no need to scan the music collection before starting
  Mopidy. Everything is read from the file system when needed and changes to
  the file system is thus immediately visible in Mopidy clients.

- Because there is no index, there is no support for search.

Our long term plan is to keep this very simple file backend in Mopidy, as it
has a well defined and limited scope, while splitting the more feature rich
Mopidy-Local extension out to an independent project. (Fixes: :issue:`1004`,
PR: :issue:`1207`)

M3U backend
-----------

- Support loading UTF-8 encoded M3U files with the ``.m3u8`` file extension.
  (PR: :issue:`1193`)

MPD frontend
------------

- The MPD command ``count`` now ignores tracks with no length, which would
  previously cause a :exc:`TypeError`. (PR: :issue:`1192`)

- Concatenate multiple artists, composers and performers using the "A;B" format
  instead of "A, B". This is a part of updating our protocol implementation to
  match MPD 0.19. (PR: :issue:`1213`)

- Add "not implemented" skeletons of new commands in the MPD protocol version
  0.19:

  - Current playlist:

    - ``rangeid``
    - ``addtagid``
    - ``cleartagid``

  - Mounts and neighbors:

    - ``mount``
    - ``unmount``
    - ``listmounts``
    - ``listneighbors``

  - Music DB:

    - ``listfiles``

- Track data now include the ``Last-Modified`` field if set on the track model.
  (Fixes: :issue:`1218`, PR: :issue:`1219`)

- Implement ``tagtypes`` MPD command. (PR: :issue:`1235`)

- Exclude empty tags fields from metadata output. (Fixes: :issue:`1045`, PR:
  :issue:`1235`)

- Implement protocol extensions to output Album URIs and Album Images when
  outputting track data to clients. (PR: :issue:`1230`)

- The MPD commands ``lsinfo`` and ``listplaylists`` are now implemented using
  the :meth:`~mopidy.core.PlaylistsController.as_list` method, which retrieves
  a lot less data and is thus much faster than the deprecated
  :meth:`~mopidy.core.PlaylistsController.get_playlists`. The drawback is that
  the ``Last-Modified`` timestamp is not available through this method, and the
  timestamps in the MPD command responses are now always set to the current
  time.

Internal changes
----------------

- Tests have been cleaned up to stop using deprecated APIs where feasible.
  (Partial fix: :issue:`1083`, PR: :issue:`1090`)


v1.0.8 (2015-07-22)
===================

Bug fix release.

- Fix reversal of ``Title`` and ``Name`` in MPD protocol (Fixes: :issue:`1212`
  PR: :issue:`1214`)

- Fix crash if an M3U file in the :confval:`m3u/playlist_dir` directory has a
  file name not decodable with the current file system encoding. (Fixes:
  :issue:`1209`)


v1.0.7 (2015-06-26)
===================

Bug fix release.

- Fix error in the MPD command ``list title ...``. The error was introduced in
  v1.0.6.


v1.0.6 (2015-06-25)
===================

Bug fix release.

- Core/MPD/Local: Add support for ``title`` in
  :meth:`mopidy.core.LibraryController.get_distinct`. (Fixes: :issue:`1181`,
  PR: :issue:`1183`)

- Core: Make sure track changes make it to audio while paused.
  (Fixes: :issue:`1177`, PR: :issue:`1185`)


v1.0.5 (2015-05-19)
===================

Bug fix release.

- Core: Add workaround for playlist providers that do not support
  creating playlists.  (Fixes: :issue:`1162`, PR :issue:`1165`)

- M3U: Fix encoding error when saving playlists with non-ASCII track
  titles. (Fixes: :issue:`1175`, PR :issue:`1176`)


v1.0.4 (2015-04-30)
===================

Bug fix release.

- Audio: Since all previous attempts at tweaking the queuing for :issue:`1097`
  seems to break things in subtle ways for different users. We are giving up
  on tweaking the defaults and just going to live with a bit more lag on
  software volume changes. (Fixes: :issue:`1147`)


v1.0.3 (2015-04-28)
===================

Bug fix release.

- HTTP: Another follow-up to the Tornado <3.0 fixing. Since the tests aren't
  run for Tornado 2.3 we didn't catch that our previous fix wasn't sufficient.
  (Fixes: :issue:`1153`, PR: :issue:`1154`)

- Audio: Follow-up fix for :issue:`1097` still exhibits issues for certain
  setups. We are giving this get an other go by setting the buffer size to
  maximum 100ms instead of a fixed number of buffers. (Addresses:
  :issue:`1147`,  PR: :issue:`1154`)


v1.0.2 (2015-04-27)
===================

Bug fix release.

- HTTP: Make event broadcasts work with Tornado 2.3 again. The threading fix
  in v1.0.1 broke this.

- Audio: Fix for :issue:`1097` tuned down the buffer size in the queue. Turns
  out this can cause distortions in certain cases. Give this an other go with
  a more generous buffer size. (Addresses: :issue:`1147`, PR: :issue:`1152`)

- Audio: Make sure mute events get emitted by software mixer.
  (Fixes: :issue:`1146`, PR: :issue:`1152`)


v1.0.1 (2015-04-23)
===================

Bug fix release.

- Core: Make the new history controller available for use. (Fixes: :js:`6`)

- Audio: Software volume control has been reworked to greatly reduce the delay
  between changing the volume and the change taking effect. (Fixes:
  :issue:`1097`, PR: :issue:`1101`)

- Audio: As a side effect of the previous bug fix, software volume is no longer
  tied to the PulseAudio application volume when using ``pulsesink``. This
  behavior was confusing for many users and doesn't work well with the plans
  for multiple outputs.

- Audio: Update scanner to decode all media it finds. This should fix cases
  where the scanner hangs on non-audio files like video. The scanner will now
  also let us know if we found any decodeable audio. (Fixes: :issue:`726`, PR:
  issue:`1124`)

- HTTP: Fix threading bug that would cause duplicate delivery of WS messages.
  (PR: :issue:`1127`)

- MPD: Fix case where a playlist that is present in both browse and as a listed
  playlist breaks the MPD frontend protocol output. (Fixes :issue:`1120`, PR:
  :issue:`1142`)


v1.0.0 (2015-03-25)
===================

Three months after our fifth anniversary, Mopidy 1.0 is finally here!

Since the release of 0.19, we've closed or merged approximately 140 issues and
pull requests through more than 600 commits by a record high 19 extraordinary
people, including seven newcomers. Thanks to :ref:`everyone <authors>` who has
:ref:`contributed <contributing>`!

For the longest time, the focus of Mopidy 1.0 was to be another incremental
improvement, to be numbered 0.20. The result is still very much an incremental
improvement, with lots of small and larger improvements across Mopidy's
functionality.

The major features of Mopidy 1.0 are:

- :ref:`Semantic Versioning <versioning>`. We promise to not break APIs before
  Mopidy 2.0. A Mopidy extension working with Mopidy 1.0 should continue to
  work with all Mopidy 1.x releases.

- Preparation work to ease migration to a cleaned up and leaner core API in
  Mopidy 2.0, and to give us some of the benefits of the cleaned up core API
  right away.

- Preparation work to enable gapless playback in an upcoming 1.x release.

Dependencies
------------

Since the previous release there are no changes to Mopidy's dependencies.
However, porting from GStreamer 0.10 to 1.x and support for running Mopidy with
Python 3.4+ is not far off on our roadmap.

Core API
--------

In the API used by all frontends and web extensions there is lots of methods
and arguments that are now deprecated in preparation for the next major
release. With the exception of some internals that leaked out in the playback
controller, no core APIs have been removed in this release. In other words,
most clients should continue to work unchanged when upgrading to Mopidy 1.0.
Though, it is strongly encouraged to review any use of the deprecated parts of
the API as those parts will be removed in Mopidy 2.0.

- **Deprecated:** Deprecate all Python properties in the core API. The
  previously undocumented getter and setter methods are now the official API.
  This aligns the Python API with the WebSocket/JavaScript API. Python
  frontends needs to be updated. WebSocket/JavaScript API users are not
  affected. (Fixes: :issue:`952`)

- Add :class:`mopidy.core.HistoryController` which keeps track of what tracks
  have been played. (Fixes: :issue:`423`, :issue:`1056`, PR: :issue:`803`,
  :issue:`1063`)

- Add :class:`mopidy.core.MixerController` which keeps track of volume and
  mute. (Fixes: :issue:`962`)

Core library controller
^^^^^^^^^^^^^^^^^^^^^^^

- **Deprecated:** :meth:`mopidy.core.LibraryController.find_exact`. Use
  :meth:`mopidy.core.LibraryController.search` with the ``exact`` keyword
  argument set to :class:`True`.

- **Deprecated:** The ``uri`` argument to
  :meth:`mopidy.core.LibraryController.lookup`. Use new ``uris`` keyword
  argument instead.

- Add ``exact`` keyword argument to
  :meth:`mopidy.core.LibraryController.search`.

- Add ``uris`` keyword argument to :meth:`mopidy.core.LibraryController.lookup`
  which allows for simpler lookup of multiple URIs. (Fixes: :issue:`1008`, PR:
  :issue:`1047`)

- Updated :meth:`mopidy.core.LibraryController.search` and
  :meth:`mopidy.core.LibraryController.find_exact` to normalize and warn about
  malformed queries from clients. (Fixes: :issue:`1067`, PR: :issue:`1073`)

- Add :meth:`mopidy.core.LibraryController.get_distinct` for getting unique
  values for a given field. (Fixes: :issue:`913`, PR: :issue:`1022`)

- Add :meth:`mopidy.core.LibraryController.get_images` for looking up images
  for any URI that is known to the backends. (Fixes :issue:`973`, PR:
  :issue:`981`, :issue:`992` and :issue:`1013`)

Core playlist controller
^^^^^^^^^^^^^^^^^^^^^^^^

- **Deprecated:** :meth:`mopidy.core.PlaylistsController.get_playlists`. Use
  :meth:`~mopidy.core.PlaylistsController.as_list` and
  :meth:`~mopidy.core.PlaylistsController.get_items` instead. (Fixes:
  :issue:`1057`, PR: :issue:`1075`)

- **Deprecated:** :meth:`mopidy.core.PlaylistsController.filter`. Use
  :meth:`~mopidy.core.PlaylistsController.as_list` and filter yourself.

- Add :meth:`mopidy.core.PlaylistsController.as_list`. (Fixes: :issue:`1057`,
  PR: :issue:`1075`)

- Add :meth:`mopidy.core.PlaylistsController.get_items`. (Fixes: :issue:`1057`,
  PR: :issue:`1075`)

Core tracklist controller
^^^^^^^^^^^^^^^^^^^^^^^^^

- **Removed:** The following methods were documented as internal. They are now
  fully private and unavailable outside the core actor. (Fixes: :issue:`1058`,
  PR: :issue:`1062`)

  - :meth:`mopidy.core.TracklistController.mark_played`
  - :meth:`mopidy.core.TracklistController.mark_playing`
  - :meth:`mopidy.core.TracklistController.mark_unplayable`

- Add ``uris`` argument to :meth:`mopidy.core.TracklistController.add` which
  allows for simpler addition of multiple URIs to the tracklist. (Fixes:
  :issue:`1060`, PR: :issue:`1065`)

Core playback controller
^^^^^^^^^^^^^^^^^^^^^^^^

- **Removed:** Remove several internal parts that were leaking into the public
  API and was never intended to be used externally. (Fixes: :issue:`1070`, PR:
  :issue:`1076`)

  - :meth:`mopidy.core.PlaybackController.change_track` is now internal.

  - Removed ``on_error_step`` keyword argument from
    :meth:`mopidy.core.PlaybackController.play`

  - Removed ``clear_current_track`` keyword argument to
    :meth:`mopidy.core.PlaybackController.stop`.

  - Made the following event triggers internal:

    - :meth:`mopidy.core.PlaybackController.on_end_of_track`
    - :meth:`mopidy.core.PlaybackController.on_stream_changed`
    - :meth:`mopidy.core.PlaybackController.on_tracklist_changed`

  - :meth:`mopidy.core.PlaybackController.set_current_tl_track` is now
    internal.

- **Deprecated:** The old methods on :class:`mopidy.core.PlaybackController`
  for volume and mute management have been deprecated. Use
  :class:`mopidy.core.MixerController` instead. (Fixes: :issue:`962`)

- When seeking while paused, we no longer change to playing. (Fixes:
  :issue:`939`, PR: :issue:`1018`)

- Changed :meth:`mopidy.core.PlaybackController.play` to take the return value
  from :meth:`mopidy.backend.PlaybackProvider.change_track` into account when
  determining the success of the :meth:`~mopidy.core.PlaybackController.play`
  call. (PR: :issue:`1071`)

- Add :meth:`mopidy.core.Listener.stream_title_changed` and
  :meth:`mopidy.core.PlaybackController.get_stream_title` for letting clients
  know about the current title in streams. (PR: :issue:`938`, :issue:`1030`)

Backend API
-----------

In the API implemented by all backends there have been way fewer but somewhat
more drastic changes with some methods removed and new ones being required for
certain functionality to continue working. Most backends were already updated
to be compatible with Mopidy 1.0 before the release. New versions of the
backends will be released shortly after Mopidy itself.

Backend library providers
^^^^^^^^^^^^^^^^^^^^^^^^^

- **Removed:** Remove :meth:`mopidy.backend.LibraryProvider.find_exact`.

- Add an ``exact`` keyword argument to
  :meth:`mopidy.backend.LibraryProvider.search` to replace the old
  :meth:`~mopidy.backend.LibraryProvider.find_exact` method.

Backend playlist providers
^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Removed:** Remove default implementation of
  :attr:`mopidy.backend.PlaylistsProvider.playlists`. This is potentially
  backwards incompatible. (PR: :issue:`1046`)

- Changed the API for :class:`mopidy.backend.PlaylistsProvider`. Note that this
  change is **not** backwards compatible. These changes are important to reduce
  the Mopidy startup time. (Fixes: :issue:`1057`, PR: :issue:`1075`)

  - Add :meth:`mopidy.backend.PlaylistsProvider.as_list`.

  - Add :meth:`mopidy.backend.PlaylistsProvider.get_items`.

  - Remove :attr:`mopidy.backend.PlaylistsProvider.playlists` property.

Backend playback providers
^^^^^^^^^^^^^^^^^^^^^^^^^^

- Changed the API for :class:`mopidy.backend.PlaybackProvider`. Note that this
  change is **not** backwards compatible for certain backends. These changes
  are crucial to adding gapless in one of the upcoming releases.
  (Fixes: :issue:`1052`, PR: :issue:`1064`)

  - :meth:`mopidy.backend.PlaybackProvider.translate_uri` has been added. It is
    strongly recommended that all backends migrate to using this API for
    translating "Mopidy URIs" to real ones for playback.

  - The semantics and signature of :meth:`mopidy.backend.PlaybackProvider.play`
    has changed. The method is now only used to set the playback state to
    playing, and no longer takes a track.

    Backends must migrate to
    :meth:`mopidy.backend.PlaybackProvider.translate_uri` or
    :meth:`mopidy.backend.PlaybackProvider.change_track` to continue working.

  - :meth:`mopidy.backend.PlaybackProvider.prepare_change` has been added.

Models
------

- Add :class:`mopidy.models.Image` model to be returned by
  :meth:`mopidy.core.LibraryController.get_images`. (Part of :issue:`973`)

- Change the semantics of :attr:`mopidy.models.Track.last_modified` to be
  milliseconds instead of seconds since Unix epoch, or a simple counter,
  depending on the source of the track. This makes it match the semantics of
  :attr:`mopidy.models.Playlist.last_modified`. (Fixes: :issue:`678`, PR:
  :issue:`1036`)

Commands
--------

- Make the ``mopidy`` command print a friendly error message if the
  :mod:`gobject` Python module cannot be imported. (Fixes: :issue:`836`)

- Add support for repeating the :option:`-v <mopidy -v>` argument four times
  to set the log level for all loggers to the lowest possible value, including
  log records at levels lower than ``DEBUG`` too.

- Add path to the current ``mopidy`` executable to the output of ``mopidy
  deps``. This make it easier to see that a user is using pip-installed Mopidy
  instead of APT-installed Mopidy without asking for ``which mopidy`` output.

Configuration
-------------

- Add support for the log level value ``all`` to the loglevels configurations.
  This can be used to show absolutely all log records, including those at
  custom levels below ``DEBUG``.

- Add debug logging of unknown sections. (Fixes: :issue:`694`, PR:
  :issue:`1002`)

Logging
-------

- Add custom log level ``TRACE`` (numerical level 5), which can be used by
  Mopidy and extensions to log at an even more detailed level than ``DEBUG``.

- Add support for per logger color overrides. (Fixes: :issue:`808`, PR:
  :issue:`1005`)

Local backend
-------------

- Improve error logging for scanner. (Fixes: :issue:`856`, PR: :issue:`874`)

- Add symlink support with loop protection to file finder. (Fixes:
  :issue:`858`, PR: :issue:`874`)

- Add ``--force`` option for ``mopidy local scan`` for forcing a full rescan of
  the library. (Fixes: :issue:`910`, PR: :issue:`1010`)

- Stop ignoring ``offset`` and ``limit`` in searches when using the default
  JSON backed local library. (Fixes: :issue:`917`, PR: :issue:`949`)

- Removed double triggering of ``playlists_loaded`` event.
  (Fixes: :issue:`998`, PR: :issue:`999`)

- Cleanup and refactoring of local playlist code. Preserves playlist names
  better and fixes bug in deletion of playlists. (Fixes: :issue:`937`,
  PR: :issue:`995` and rebased into :issue:`1000`)

- Sort local playlists by name. (Fixes: :issue:`1026`, PR: :issue:`1028`)

- Moved playlist support out to a new extension, :ref:`ext-m3u`.

- *Deprecated:* The config value :confval:`local/playlists_dir` is no longer in
  use and can be removed from your config.

Local library API
^^^^^^^^^^^^^^^^^

- Implementors of :meth:`mopidy.local.Library.lookup` should now return a list
  of :class:`~mopidy.models.Track` instead of a single track, just like the
  other ``lookup()`` methods in Mopidy. For now, returning a single track will
  continue to work. (PR: :issue:`840`)

- Add support for giving local libraries direct access to tags and duration.
  (Fixes: :issue:`967`)

- Add :meth:`mopidy.local.Library.get_images` for looking up images
  for local URIs. (Fixes: :issue:`1031`, PR: :issue:`1032` and :issue:`1037`)

Stream backend
--------------

- Add support for HTTP proxies when doing initial metadata lookup for a stream.
  (Fixes :issue:`390`, PR: :issue:`982`)

- Add basic tests for the stream library provider.

M3U backend
-----------

- Mopidy-M3U is a new bundled backend. It provides the same M3U support as was
  previously part of the local backend. See :ref:`m3u-migration` for how to
  migrate your local playlists to work with the M3U backend. (Fixes:
  :issue:`1054`, PR: :issue:`1066`)

- In playlist names, replace "/", which are illegal in M3U file names,
  with "|". (PR: :issue:`1084`)

MPD frontend
------------

- Add support for blacklisting MPD commands. This is used to prevent clients
  from using ``listall`` and ``listallinfo`` which recursively lookup the
  entire "database". If you insist on using a client that needs these commands
  change :confval:`mpd/command_blacklist`.

- Start setting the ``Name`` field with the stream title when listening to
  radio streams. (Fixes: :issue:`944`, PR: :issue:`1030`)

- Enable browsing of artist references, in addition to albums and playlists.
  (PR: :issue:`884`)

- Switch the ``list`` command over to using the new method
  :meth:`mopidy.core.LibraryController.get_distinct` for increased performance.
  (Fixes: :issue:`913`)

- In stored playlist names, replace "/", which are illegal, with "|" instead of
  a whitespace. Pipes are more similar to forward slash.

- Share a single mapping between names and URIs across all MPD sessions.
  (Fixes: :issue:`934`, PR: :issue:`968`)

- Add support for ``toggleoutput`` command. (PR: :issue:`1015`)

- The ``mixrampdb`` and ``mixrampdelay`` commands are now known to Mopidy, but
  are not implemented. (PR: :issue:`1015`)

- Fix crash on socket error when using a locale causing the exception's error
  message to contain characters not in ASCII. (Fixes: issue:`971`, PR:
  :issue:`1044`)

HTTP frontend
-------------

- **Deprecated:** Deprecated the :confval:`http/static_dir` config. Please make
  your web clients pip-installable Mopidy extensions to make it easier to
  install for end users.

- Prevent a race condition in WebSocket event broadcasting from crashing the
  web server. (PR: :issue:`1020`)

Mixers
------

- Add support for disabling volume control in Mopidy entirely by setting the
  configuration :confval:`audio/mixer` to ``none``. (Fixes: :issue:`936`, PR:
  :issue:`1015`, :issue:`1035`)

Audio
-----

- **Removed:** Support for visualizers and the :confval:`audio/visualizer`
  config value. The feature was originally added as a workaround for all the
  people asking for ncmpcpp visualizer support, and since we could get it
  almost for free thanks to GStreamer. But, this feature did never make sense
  for a server such as Mopidy.

- **Deprecated:** Deprecated :meth:`mopidy.audio.Audio.emit_end_of_stream`.
  Pass a :class:`None` buffer to :meth:`mopidy.audio.Audio.emit_data` to end
  the stream. This should only affect Mopidy-Spotify.

- Add :meth:`mopidy.audio.AudioListener.tags_changed`. Notifies core when new
  tags are found.

- Add :meth:`mopidy.audio.Audio.get_current_tags` for looking up the current
  tags of the playing media.

- Internal code cleanup within audio subsystem:

  - Started splitting audio code into smaller better defined pieces.

  - Improved GStreamer related debug logging.

  - Provide better error messages for missing plugins.

  - Add foundation for trying to re-add multiple output support.

  - Add internal helper for converting GStreamer data types to Python.

  - Reduce scope of audio scanner to just find tags and duration. Modification
    time, URI and minimum length handling are now outside of this class.

  - Update scanner to operate with milliseconds for duration.

  - Update scanner to use a custom source, typefind and decodebin. This allows
    us to detect playlists before we try to decode them.

  - Refactored scanner to create a new pipeline per track, this is needed as
    reseting decodebin is much slower than tearing it down and making a fresh
    one.

- Move and rename helper for converting tags to tracks.

- Ignore albums without a name when converting tags to tracks.

- Support UTF-8 in M3U playlists. (Fixes: :issue:`853`)

- Add workaround for volume not persisting across tracks on OS X.
  (Issue: :issue:`886`, PR: :issue:`958`)

- Improved missing plugin error reporting in scanner. (PR: :issue:`1033`)

- Introduced a new return type for the scanner, a named tuple with ``uri``,
  ``tags``, ``duration``, ``seekable`` and ``mime``. (PR: :issue:`1033`)

- Added support for checking if the media is seekable, and getting the initial
  MIME type guess. (PR: :issue:`1033`)

Mopidy.js client library
------------------------

This version has been released to npm as Mopidy.js v0.5.0.

- Reexport When.js library as ``Mopidy.when``, to make it easily available to
  users of Mopidy.js. (Fixes: :js:`1`)

- Default to ``wss://`` as the WebSocket protocol if the page is hosted on
  ``https://``. This has no effect if the ``webSocketUrl`` setting is
  specified. (Pull request: :js:`2`)

- Upgrade dependencies.

Development
-----------

- Add new :ref:`contribution guidelines <contributing>`.

- Add new :ref:`development guide <devenv>`.

- Speed up event emitting.

- Changed test runner from nose to py.test. (PR: :issue:`1024`)
