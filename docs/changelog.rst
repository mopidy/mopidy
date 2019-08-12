.. _changelog:

*********
Changelog
*********

This changelog is used to track all major changes to Mopidy.

For older releases, see :ref:`history`.


v3.0.0 (UNRELEASED)
===================

Backwards incompatible release.

Dependencies
------------

- Pykka >= 2.0 is now required.

- We now use a number of constants and functions from ``GLib`` instead of their
  deprecated equivalents in ``GObject``. The exact version of PyGObject and
  GLib that makes these constants and functions available in the new location
  is not known, but is believed to have been released in 2015 or earlier.

Logging
-------

- The command line option :option:`mopidy --save-debug-log` and the
  configuration :confval:`logging/debug_file` have been removed.
  To save a debug log for sharing, run ``mopidy -vvvv | tee mopidy.log``
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
  This does not work with online music services,
  and have thus been deprecated since 1.0.

History controller
^^^^^^^^^^^^^^^^^^

- (no changes yet)

Mixer controller
^^^^^^^^^^^^^^^^

- (no changes yet)

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

- Removed the support for passing filter criterias as keyword arguments to
  :meth:`mopidy.core.TracklistController.filter`.
  Use the ``criteria`` argument instead.

- Removed the support for passing filter criterias as keyword arguments to
  :meth:`mopidy.core.TracklistController.remove`.
  Use the ``criteria`` argument instead.

Backend API
-----------

- (no changes yet)

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

- (no changes yet)

HTTP frontend
-------------

- Stop bundling Mopidy.js and serving it at ``/mopidy/mopidy.js`` and
  ``/mopidy/mopidy.min.js``. All Mopidy web clients must use Mopidy.js from npm
  or vendor their own copy of the library.
  (Fixes: :issue:`1083`, :issue:`1460`, PR: :issue:`1708`)

- Remove support for serving arbitrary files over HTTP through the use of
  :confval:`http/static_dir`, which has been deprecated since 1.0. (Fixes:
  :issue:`1463`, PR: :issue:`1706`)

MPD frontend
------------

- Improved the ``swap`` command to swap the tracks without rebuilding
  the full tracklist.

File backend
------------

- (no changes yet)

Local backend
-------------

- The Mopidy-Local backend is no longer bundled with Mopidy, and has been moved
  to its own `Git repo <https://github.com/mopidy/mopidy-local>`__ and
  `PyPI project <https://pypi.org/project/Mopidy-Local>`__.
  (Fixes: :issue:`1003`)

M3U backend
-----------

- (no changes yet)

Stream backend
--------------

- (no changes yet)

Audio
-----

- Remove the method :meth:`mopidy.audio.Audio.emit_end_of_stream`, which has
  been deprecated since 1.0. (Fixes: :issue:`1465`, PR: :issue:`1705`)


v2.2.4 (UNRELEASED)
===================

Bug fix release.

- Fix `PkgResourcesDeprecationWarning` on startup when a recent release
  of setuptools is installed. (Fixes: :issue:`1778`, PR: :issue:`1780`)

- Network: Close connection following an exception in the protocol handler.
  (Fixes: :issue:`1762`, PR: :issue:`1765`)


v2.2.3 (2019-06-20)
===================

Bug fix release.

- Audio: Fix switching between tracks with different sample rates. (Fixes:
  :issue:`1528`, PR: :issue:`1735`)

- Audio: Prevent buffering handling interfering with track changes. (Fixes:
  :issue:`1722`, PR: :issue:`1740`)

- Local: Add ``.pdf`` and ``.zip`` to the default
  :confval:`local/excluded_file_extensions` config value. (PR: :issue:`1737`)

- File: Synchronised the default :confval:`file/excluded_file_extensions`
  config values with :confval:`local/excluded_file_extensions`. (PR:
  :issue:`1743`)

- Stream: Fix error when playing stream from ``.pls`` playlist with quoted
  URLs. (Fixes: :issue:`1770`, PR: :issue:`1771`)

- Docs: Resize and compress images, reducing the release tarball size from 3.5
  to 1.1 MB.

- Docs: Fix broken links.


v2.2.2 (2018-12-29)
===================

Bug fix release.

- HTTP: Fix hang on exit due to change in Tornado v5.0 IOLoop. (Fixes:
  :issue:`1715`, PR: :issue:`1716`)

- Files: Fix crash due to mix of text and bytes in paths that come from
  ``$XDG_CONFIG_HOME/user-dirs.dirs``. (Fixes: :issue:`1676`, :issue:`1725`)


v2.2.1 (2018-10-15)
===================

Bug fix release.

- HTTP: Stop blocking connections where the network location part of the
  ``Origin`` header is empty, such as WebSocket connections originating from
  local files. (Fixes: :issue:`1711`, PR: :issue:`1712`)

- HTTP: Add new config value :confval:`http/csrf_protection` which enables all
  CSRF protections introduced in Mopidy 2.2.0. It is enabled by default and
  should only be disabled by those users who are unable to set a
  ``Content-Type: application/json`` request header or cannot utilise the
  :confval:`http/allowed_origins` config value. (Fixes: :issue:`1713`, PR:
  :issue:`1714`)


v2.2.0 (2018-09-30)
===================

Mopidy 2.2.0, a feature release, is out. It is a quite small release, featuring
mostly minor fixes and improvements.

Most notably, this release introduces CSRF protection for both the HTTP and
WebSocket RPC interfaces, and improves the file path checking in the M3U
backend. The CSRF protection should stop attacks against local Mopidy servers
from malicious websites, like what was demonstrated by Josef Gajdusek in
:issue:`1659`.

Since the release of 2.1.0, we've closed approximately 21 issues and pull
requests through 133 commits by 22 authors.

- Dependencies: Drop support for Tornado < 4.4. Though strictly a breaking
  change, this shouldn't affect any supported systems as even Debian stable
  includes Tornado >= 4.4.

- Core: Remove upper limit of 10000 tracks in tracklist. 10000 tracks is still
  the default limit as some MPD clients crash if the tracklist is longer, but
  it is now possible to set the :confval:`core/max_tracklist_length` config
  value as high as you want to. (Fixes: :issue:`1600`, PR: :issue:`1666`)

- Core: Fix crash on ``library.lookup(uris=[])``. (Fixes: :issue:`1619`, PR:
  :issue:`1620`)

- Core: Define return value of ``playlists.delete()`` to be a bool,
  :class:`True` on success, :class:`False` otherwise. (PR: :issue:`1702`)

- M3U: Ignore all attempts at accessing files outside the
  :confval:`m3u/playlist_dir`. (Partly fixes: :issue:`1659`, PR: :issue:`1702`)

- File: Change default ordering to show directories first, then files. (PR:
  :issue:`1595`)

- File: Fix extraneous encoding of path. (PR: :issue:`1611`)

- HTTP: Protect RPC and WebSocket interfaces against CSRF by blocking requests
  that originate from servers other than those specified in the new config
  value :confval:`http/allowed_origins`. An artifact of this is that all
  JSON-RPC requests must now always set the header
  ``Content-Type: application/json``.
  (Partly fixes: :issue:`1659`, PR: :issue:`1668`)

- MPD: Added ``idle`` to the list of available commands.
  (Fixes: :issue:`1593`, PR: :issue:`1597`)

- MPD: Added Unix domain sockets for binding MPD to.
  (Fixes: :issue:`1531`, PR: :issue:`1629`)

- MPD: Lookup track metadata for MPD ``load`` and ``listplaylistinfo``.
  (Fixes: :issue:`1511`, PR: :issue:`1621`)

- Ensure that decoding of OS errors with unknown encoding never crashes, but
  instead replaces unknown bytes with a replacement marker. (Fixes:
  :issue:`1599`)

- Set GLib program and application name, so that we show up as "Mopidy" in
  PulseAudio instead of "python ...". (PR: :issue:`1626`)


v2.1.0 (2017-01-02)
===================

Mopidy 2.1.0, a feature release, is finally out!

Since the release of 2.0.0, it has been quiet times in Mopidy circles. This is
mainly caused by core developers moving from the enterprise to startups or into
positions with more responsibility, and getting more kids. Of course, this has
greatly decreased the amount of spare time available for open source work. But
fear not, Mopidy is not dead. We've returned from year long periods with close
to no activity before, and will hopefully do so again.

Despite all, we've closed or merged approximately 18 issues and pull requests
through about 170 commits since the release of v2.0.1 back in August.

The major new feature in Mopidy 2.1 is support for restoring playback state and
the current playlist after a restart. This feature was contributed by `Jens
Lütjen <https://github.com/dublok>`_.

- Dependencies: Drop support for Tornado < 3.2. Though strictly a breaking
  change, this shouldn't have any effect on what systems we support, as Tornado
  3.2 or newer is available from the distros that include GStreamer >= 1.2.3,
  which we already require.

- Core: Mopidy restores its last state when started. Can be enabled by setting
  the config value :confval:`core/restore_state` to ``true``.

- Audio: Update scanner to handle sources such as RTSP. (Fixes: :issue:`1479`)

- Audio: The scanner set the date to :attr:`mopidy.models.Track.date` and
  :attr:`mopidy.models.Album.date`
  (Fixes: :issue:`1741`)

- File: Add new config value :confval:`file/excluded_file_extensions`.

- Local: Skip hidden directories directly in ``media_dir``.
  (Fixes: :issue:`1559`, PR: :issue:`1555`)

- MPD: Fix MPD protocol for ``replay_gain_status`` command. The actual command
  remains unimplemented. (PR: :issue:`1520`)

- MPD: Add ``nextsong`` and ``nextsongid`` to the response of MPD ``status``
  command. (Fixes: :issue:`1133`, :issue:`1516`, PR: :issue:`1523`)

- MPD: Fix inconsistent playlist state after playlist is emptied with repeat
  and consume mode turned on. (Fixes: :issue:`1512`, PR: :issue:`1549`)

- Audio: Improve handling of duration in scanning. VBR tracks should fail less
  frequently and MMS works again. (Fixes: :issue:`1553`, PR :issue:`1575`,
  :issue:`1576`, :issue:`1577`)


v2.0.1 (2016-08-16)
===================

Bug fix release.

- Audio: Set ``soft-volume`` flag on GStreamer's playbin element. This is the
  playbin's default, but we managed to override it when configuring the playbin
  to only process audio. This should fix the "Volume/mute is not available"
  warning.

- Audio: Fix buffer conversion. This fixes image extraction.
  (Fixes: :issue:`1469`, PR: :issue:`1472`)

- Audio: Update scan logic to workaround GStreamer issue where tags and
  duration might only be available after we start playing.
  (Fixes: :issue:`935`, :issue:`1453`, :issue:`1474`, :issue:`1480`, PR:
  :issue:`1487`)

- Audio: Better handling of seek when position does not match the expected
  pending position. (Fixes: :issue:`1462`, :issue:`1505`, PR: :issue:`1496`)

- Audio: Handle bad date tags from audio, thanks to Mario Lang and Tom Parker
  who fixed this in parallel. (Fixes: :issue:`1506`, PR: :issue:`1525`,
  :issue:`1517`)

- Audio: Make sure scanner handles streams without a duration.
  (Fixes: :issue:`1526`)

- Audio: Ensure audio tags are never ``None``. (Fixes: :issue:`1449`)

- Audio: Update :meth:`mopidy.audio.Audio.set_metadata` to postpone sending
  tags if there is a pending track change. (Fixes: :issue:`1357`, PR:
  :issue:`1538`)

- Core: Avoid endless loop if all tracks in the tracklist are unplayable and
  consume mode is off. (Fixes: :issue:`1221`, :issue:`1454`, PR: :issue:`1455`)

- Core: Correctly record the last position of a track when switching to another
  one. Particularly relevant for Mopidy-Scrobbler users, as before it was
  essentially unusable. (Fixes: :issue:`1456`, PR: :issue:`1534`)

- Models: Fix encoding error if :class:`~mopidy.models.fields.Identifier`
  fields, like the ``musicbrainz_id`` model fields, contained non-ASCII Unicode
  data. (Fixes: :issue:`1508`, PR: :issue:`1546`)

- File: Ensure path comparison is done between bytestrings only. Fixes crash
  where a :confval:`file/media_dirs` path contained non-ASCII characters.
  (Fixes: :issue:`1345`, PR: :issue:`1493`)

- Stream: Fix milliseconds vs seconds mistake in timeout handling.
  (Fixes: :issue:`1521`, PR: :issue:`1522`)

- Docs: Fix the rendering of :class:`mopidy.core.Core` and
  :class:`mopidy.audio.Audio` docs. This should also contribute towards making
  the Mopidy Debian package build bit-by-bit reproducible. (Fixes:
  :issue:`1500`)


v2.0.0 (2016-02-15)
===================

Mopidy 2.0 is here!

Since the release of 1.1, we've closed or merged approximately 80 issues and
pull requests through about 350 commits by 14 extraordinary people, including
10 newcomers. That's about the same amount of issues and commits as between 1.0
and 1.1. The number of contributors is a bit lower but we didn't have a real
life sprint during this development cycle. Thanks to :ref:`everyone <authors>`
who has :ref:`contributed <contributing>`!

With the release of Mopidy 1.0 we promised that any extension working with
Mopidy 1.0 should continue working with all Mopidy 1.x releases. Mopidy 2.0 is
quite a friendly major release and will only break a single extension that we
know of: Mopidy-Spotify. To ensure that everything continues working, please
upgrade to Mopidy 2.0 and Mopidy-Spotify 3.0 at the same time.

No deprecated functionality has been removed in Mopidy 2.0.

The major features of Mopidy 2.0 are:

- Gapless playback has been mostly implemented. It works as long as you don't
  change tracks in the middle of a track or use previous and next. In a future
  release, previous and next will also become gapless. It is now quite easy to
  have Mopidy streaming audio over the network using Icecast. See the updated
  :ref:`streaming` docs for details of how to set it up and workarounds for the
  remaining issues.

- Mopidy has upgraded from GStreamer 0.10 to 1.x. This has been in our backlog
  for more than three years. With this upgrade we're ridding ourselves of
  years of GStreamer bugs that have been fixed in newer releases, we can get
  into Debian testing again, and we've removed the last major roadblock for
  running Mopidy on Python 3.

Dependencies
------------

- Mopidy now requires GStreamer >= 1.2.3, as we've finally ported from
  GStreamer 0.10. Since we're requiring a new major version of our major
  dependency, we're upping the major version of Mopidy too. (Fixes:
  :issue:`225`)

Core API
--------

- Start ``tlid`` counting at 1 instead of 0 to keep in sync with MPD's
  ``songid``.

- :meth:`~mopidy.core.PlaybackController.get_time_position` now returns the
  seek target while a seek is in progress.  This gives better results than just
  failing the position query. (Fixes: :issue:`312` PR: :issue:`1346`)

- Add :meth:`mopidy.core.PlaylistsController.get_uri_schemes`. (PR:
  :issue:`1362`)

- The ``track_playback_ended`` event now includes the correct ``tl_track``
  reference when changing to the next track in consume mode. (Fixes:
  :issue:`1402` PR: :issue:`1403` PR: :issue:`1406`)

Models
------

- **Deprecated:** :attr:`mopidy.models.Album.images` is deprecated. Use
  :meth:`mopidy.core.LibraryController.get_images` instead. (Fixes:
  :issue:`1325`)

Extension support
-----------------

- Log exception and continue if an extension crashes during setup. Previously,
  we let Mopidy crash if an extension's setup crashed. (PR: :issue:`1337`)

Local backend
-------------

- Made :confval:`local/data_dir` really deprecated. This change breaks older
  versions of Mopidy-Local-SQLite and Mopidy-Local-Images.

M3U backend
-----------

- Add :confval:`m3u/base_dir` for resolving relative paths in M3U
  files. (Fixes: :issue:`1428`, PR: :issue:`1442`)

- Derive track name from file name for non-extended M3U
  playlists. (Fixes: :issue:`1364`, PR: :issue:`1369`)

- Major refactoring of the M3U playlist extension. (Fixes:
  :issue:`1370` PR: :issue:`1386`)

  - Add :confval:`m3u/default_encoding` and :confval:`m3u/default_extension`
    config values for improved text encoding support.

  - No longer scan playlist directory and parse playlists at startup or
    refresh. Similarly tothe file extension, this now happens on request.

  - Use :class:`mopidy.models.Ref` instances when reading and writing
    playlists. Therefore, ``Track.length`` is no longer stored in
    extended M3U playlists and ``#EXTINF`` runtime is always set to
    -1.

  - Improve reliability of playlist updates using the core playlist API by
    applying the write-replace pattern for file updates.

Stream backend
--------------

- Make sure both lookup and playback correctly handle playlists and our
  blacklist support. (Fixes: :issue:`1445`, PR: :issue:`1447`)

MPD frontend
------------

- Implemented commands for modifying stored playlists:

  - ``playlistadd``
  - ``playlistclear``
  - ``playlistdelete``
  - ``playlistmove``
  - ``rename``
  - ``rm``
  - ``save``

  (Fixes: :issue:`1014`, PR: :issue:`1187`, :issue:`1308`, :issue:`1322`)

- Start ``songid`` counting at 1 instead of 0 to match the original MPD server.

- Idle events are now emitted on ``seeked`` events. This fix means that
  clients relying on ``idle`` events now get notified about seeks.
  (Fixes: :issue:`1331`, PR: :issue:`1347`)

- Idle events are now emitted on ``playlists_loaded`` events. This fix means
  that clients relying on ``idle`` events now get notified about playlist
  loads.
  (Fixes: :issue:`1331`, PR: :issue:`1347`)

- Event handler for ``playlist_deleted`` has been unbroken. This unreported bug
  would cause the MPD frontend to crash preventing any further communication
  via the MPD protocol. (PR: :issue:`1347`)

Zeroconf
--------

- Require ``stype`` argument to :class:`mopidy.zeroconf.Zeroconf`.

- Use Avahi's interface selection by default. (Fixes: :issue:`1283`)

- Use Avahi server's hostname instead of ``socket.getfqdn()`` in service
  display name.

Cleanups
--------

- Removed warning if :file:`~/.mopidy` exists. We stopped using this location
  in 0.6, released in October 2011.

- Removed warning if :file:`~/.config/mopidy/settings.py` exists. We stopped
  using this settings file in 0.14, released in April 2013.

- The ``on_event`` handler in our listener helper now catches exceptions. This
  means that any errors in event handling won't crash the actor in question.

- Catch errors when loading :confval:`logging/config_file`.
  (Fixes: :issue:`1320`)

- **Breaking:** Removed unused internal
  :class:`mopidy.internal.process.BaseThread`. This breaks Mopidy-Spotify
  1.4.0. Versions < 1.4.0 was already broken by Mopidy 1.1, while versions >=
  2.0 doesn't use this class.

Audio
-----

- **Breaking:** The audio scanner now returns ISO-8601 formatted strings
  instead of :class:`~datetime.datetime` objects for dates found in tags.
  Because of this change, we can now return years without months or days, which
  matches the semantics of the date fields in our data models.

- **Breaking:** :meth:`mopidy.audio.Audio.set_appsrc`'s ``caps`` argument has
  changed format due to the upgrade from GStreamer 0.10 to GStreamer 1. As
  far as we know, this is only used by Mopidy-Spotify. As an example, with
  GStreamer 0.10 the Mopidy-Spotify caps was::

      audio/x-raw-int, endianness=(int)1234, channels=(int)2, width=(int)16,
      depth=(int)16, signed=(boolean)true, rate=(int)44100

  With GStreamer 1 this changes to::

      audio/x-raw,format=S16LE,rate=44100,channels=2,layout=interleaved

  If your Mopidy backend uses ``set_appsrc()``, please refer to GStreamer
  documentation for details on the new caps string format.

- **Breaking:** :func:`mopidy.audio.utils.create_buffer`'s ``capabilities``
  argument is no longer in use and has been removed. As far as we know, this
  was only used by Mopidy-Spotify.

- Duplicate seek events getting to ``appsrc`` based backends is now fixed. This
  should prevent seeking in Mopidy-Spotify from glitching. (Fixes:
  :issue:`1404`)

- Workaround crash caused by a race that does not seem to affect functionality.
  This should be fixed properly together with :issue:`1222`. (Fixes:
  :issue:`1430`, PR: :issue:`1438`)

- Add a new config option, :confval:`audio/buffer_time`, for setting the buffer
  time of the GStreamer queue. If you experience buffering before track
  changes, it may help to increase this. (Workaround for :issue:`1409`)

- ``tags_changed`` events are only emitted for fields that have changed.
  Previous behavior was to emit this for all fields received from GStreamer.
  (PR: :issue:`1439`)

Gapless
-------

- Add partial support for gapless playback. Gapless now works as long as you
  don't change tracks or use next/previous. (PR: :issue:`1288`)

  The :ref:`streaming` docs has been updated with the workarounds still needed
  to properly stream Mopidy audio through Icecast.

- Core playback has been refactored to better handle gapless, and async state
  changes.

- Tests have been updated to always use a core actor so async state changes
  don't trip us up.

- Seek events are now triggered when the seek completes. Previously the event
  was emitted when the seek was requested, not when it completed. Further
  changes have been made to make seek work correctly for gapless related corner
  cases. (Fixes: :issue:`1305` PR: :issue:`1346`)
