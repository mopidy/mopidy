********************
Changelog 0.x series
********************

This is the changelog of Mopidy v0.1.0a0 through v0.19.5.

For the latest releases, see :ref:`changelog`.


v0.19.5 (2014-12-23)
====================

Today is Mopidy's five year anniversary. We're celebrating with a bugfix
release and are looking forward to the next five years!

- Config: Support UTF-8 in extension's default config. If an extension with
  non-ASCII characters in its default config was installed, and Mopidy didn't
  already have a config file, Mopidy would crashed when trying to create the
  initial config file based on the default config of all available extensions.
  (Fixes: :discuss:`428`)

- Extensions: Fix crash when unpacking data from
  :exc:`pkg_resources.VersionConflict` created with a single argument. (Fixes:
  :issue:`911`)

- Models: Hide empty collections from :func:`repr()` representations.

- Models: Field values are no longer stored on the model instance when the
  value matches the default value for the field. This makes two models equal
  when they have a field which in one case is implicitly set to the default
  value and in the other case explicitly set to the default value, but with
  otherwise equal fields. (Fixes: :issue:`837`)

- Models: Changed the default value of :attr:`mopidy.models.Album.num_tracks`,
  :attr:`mopidy.models.Track.track_no`, and
  :attr:`mopidy.models.Track.last_modified` from ``0`` to :class:`None`.

- Core: When skipping to the next track in consume mode, remove the skipped
  track from the tracklist. This is consistent with the original MPD server's
  behavior. (Fixes: :issue:`902`)

- Local: Fix scanning of modified files. (PR: :issue:`904`)

- MPD: Re-enable browsing of empty directories. (PR: :issue:`906`)

- MPD: Remove track comments from responses. They are not included by the
  original MPD server, and this works around :issue:`881`. (PR: :issue:`882`)

- HTTP: Errors while starting HTTP apps are logged instead of crashing the HTTP
  server. (Fixes: :issue:`875`)


v0.19.4 (2014-09-01)
====================

Bug fix release.

- Configuration: :option:`mopidy --config` now supports directories.

- Logging: Fix that some loggers would be disabled if
  :confval:`logging/config_file` was set. (Fixes: :issue:`740`)

- Quit process with exit code 1 when stopping because of a backend, frontend,
  or mixer initialization error.

- Backend API: Update :meth:`mopidy.backend.LibraryProvider.browse` signature
  and docs to match how the core use the backend's browse method. (Fixes:
  :issue:`833`)

- Local library API: Add :attr:`mopidy.local.Library.ROOT_DIRECTORY_URI`
  constant for use by implementors of :meth:`mopidy.local.Library.browse`.
  (Related to: :issue:`833`)

- HTTP frontend: Guard against double close of WebSocket, which causes an
  :exc:`AttributeError` on Tornado < 3.2.

- MPD frontend: Make the ``list`` command return albums when sending 3
  arguments. This was incorrectly returning artists after the MPD command
  changes in 0.19.0. (Fixes: :issue:`817`)

- MPD frontend: Fix a race condition where two threads could try to free the
  same data simultaneously. (Fixes: :issue:`781`)


v0.19.3 (2014-08-03)
====================

Bug fix release.

- Audio: Fix negative track length for radio streams. (Fixes: :issue:`662`,
  PR: :issue:`796`)

- Audio: Tell GStreamer to not pick Jack sink. (Fixes: :issue:`604`)

- Zeroconf: Fix discovery by adding ``.local`` to the announced hostname. (PR:
  :issue:`795`)

- Zeroconf: Fix intermittent DBus/Avahi exception.

- Extensions: Fail early if trying to setup an extension which doesn't
  implement the :meth:`mopidy.ext.Extension.setup` method. (Fixes:
  :issue:`813`)


v0.19.2 (2014-07-26)
====================

Bug fix release, directly from the Mopidy development sprint at EuroPython 2014
in Berlin.

- Audio: Make :confval:`audio/mixer_volume` work on the software mixer again.
  This was broken with the mixer changes in 0.19.0. (Fixes: :issue:`791`)

- HTTP frontend: When using Tornado 4.0, allow WebSocket requests from other
  hosts. (Fixes: :issue:`788`)

- MPD frontend: Fix crash when MPD commands are called with the wrong number of
  arguments.  This was broken with the MPD command changes in 0.19.0. (Fixes:
  :issue:`789`)


v0.19.1 (2014-07-23)
====================

Bug fix release.

- Dependencies: Mopidy now requires Tornado >= 2.3, instead of >= 3.1. This
  should make Mopidy continue to work on Debian/Raspbian stable, where Tornado
  2.3 is the newest version available.

- HTTP frontend: Add missing string interpolation placeholder.

- Development: ``mopidy --version`` and :meth:`mopidy.core.Core.get_version`
  now returns the correct version when Mopidy is run from a Git repo other than
  Mopidy's own. (Related to :issue:`706`)


v0.19.0 (2014-07-21)
====================

The focus of 0.19 have been on improving the MPD implementation, replacing
GStreamer mixers with our own mixer API, and on making web clients installable
with ``pip``, like any other Mopidy extension.

Since the release of 0.18, we've closed or merged 53 issues and pull requests
through about 445 commits by :ref:`12 people <authors>`, including five new
guys. Thanks to everyone that has contributed!

**Dependencies**

- Mopidy now requires Tornado >= 3.1.

- Mopidy no longer requires CherryPy or ws4py. Previously, these were optional
  dependencies required for the HTTP frontend to work.

**Backend API**

- *Breaking change:* Imports of the backend API from
  :mod:`mopidy.backends` no longer works. The new API introuced in v0.18 is now
  required. Most extensions already use the new API location.

**Commands**

- The ``mopidy-convert-config`` tool for migrating the ``setings.py``
  configuration file used by Mopidy up until 0.14 to the new config file format
  has been removed after over a year of trusty service. If you still need to
  convert your old ``settings.py`` configuration file, do so using and older
  release, like Mopidy 0.18, or migrate the configuration to the new format by
  hand.

**Configuration**

- Add ``optional=True`` support to :class:`mopidy.config.Boolean`.

**Logging**

- Fix proper decoding of exception messages that depends on the user's locale.

- Colorize logs depending on log level. This can be turned off with the new
  :confval:`logging/color` configuration. (Fixes: :issue:`772`)

**Extension support**

- *Breaking change:* Removed the :class:`~mopidy.ext.Extension` methods that
  were deprecated in 0.18: :meth:`~mopidy.ext.Extension.get_backend_classes`,
  :meth:`~mopidy.ext.Extension.get_frontend_classes`, and
  :meth:`~mopidy.ext.Extension.register_gstreamer_elements`. Use
  :meth:`mopidy.ext.Extension.setup` instead, as most extensions already do.

**Audio**

- *Breaking change:* Removed support for GStreamer mixers. GStreamer 1.x does
  not support volume control, so we changed to use software mixing by default
  in v0.17.0. Now, we're removing support for all other GStreamer mixers and
  are reintroducing mixers as something extensions can provide independently of
  GStreamer. (Fixes: :issue:`665`, PR: :issue:`760`)

- *Breaking change:* Changed the :confval:`audio/mixer` config value to refer
  to Mopidy mixer extensions instead of GStreamer mixers. The default value,
  ``software``, still has the same behavior. All other values will either no
  longer work or will at the very least require you to install an additional
  extension.

- Changed the :confval:`audio/mixer_volume` config value behavior from
  affecting GStreamer mixers to affecting Mopidy mixer extensions instead. The
  end result should be the same without any changes to this config value.

- Deprecated the :confval:`audio/mixer_track` config value. This config value
  is no longer in use. Mixer extensions that need additional configuration
  handle this themselves.

- Use :ref:`proxy-config` when streaming media from the Internet. (Partly
  fixing :issue:`390`)

- Fix proper decoding of exception messages that depends on the user's locale.

- Fix recognition of ASX and XSPF playlists with tags in all caps or with
  carriage return line endings. (Fixes: :issue:`687`)

- Support simpler ASX playlist variant with ``<ENTRY>`` elements without
  children.

- Added ``target_state`` attribute to the audio layer's
  :meth:`~mopidy.audio.AudioListener.state_changed` event. Currently, it is
  :class:`None` except when we're paused because of buffering. Then the new
  field exposes our target state after buffering has completed.

**Mixers**

- Added new :class:`mopidy.mixer.Mixer` API which can be implemented by
  extensions.

- Created a bundled extension, :ref:`ext-softwaremixer`, for controlling volume
  in software in GStreamer's pipeline. This is Mopidy's default mixer. To use
  this mixer, set the :confval:`audio/mixer` config value to ``software``.

- Created an external extension, `Mopidy-ALSAMixer
  <https://github.com/mopidy/mopidy-alsamixer/>`_, for controlling volume with
  hardware through ALSA. To use this mixer, install the extension, and set the
  :confval:`audio/mixer` config value to ``alsamixer``.

**HTTP frontend**

- CherryPy and ws4py have been replaced with Tornado. This will hopefully
  reduce CPU usage on OS X (:issue:`445`) and improve error handling in corner
  cases, like when returning from suspend (:issue:`718`).

- Added support for packaging web clients as Mopidy extensions and installing
  them using pip. See the :ref:`http-server-api` for details. (Fixes:
  :issue:`440`)

- Added web page at ``/mopidy/`` which lists all web clients installed as
  Mopidy extensions. (Fixes: :issue:`440`)

- Added support for extending the HTTP frontend with additional server side
  functionality. See :ref:`http-server-api` for details.

- Exposed the core API using HTTP POST requests with JSON-RPC payloads at
  ``/mopidy/rpc``. This is the same JSON-RPC interface as is exposed over the
  WebSocket at ``/mopidy/ws``, so you can run any core API command.

  The HTTP POST interfaces does not give you access to events from Mopidy, like
  the WebSocket does. The WebSocket interface is still recommended for web
  clients. The HTTP POST interface may be easier to use for simpler programs,
  that just needs to query the currently playing track or similar. See
  :ref:`http-post-api` for details.

- If Zeroconf is enabled, we now announce the ``_mopidy-http._tcp`` service in
  addition to ``_http._tcp``. This is to make it easier to automatically find
  Mopidy's HTTP server among other Zeroconf-published HTTP servers on the
  local network.

**Mopidy.js client library**

This version has been released to npm as Mopidy.js v0.4.0.

- Update Mopidy.js to use when.js 3. If you maintain a Mopidy client, you
  should review the `differences between when.js 2 and 3
  <https://github.com/cujojs/when/blob/master/docs/api.md#upgrading-to-30-from-2x>`_
  and the `when.js debugging guide
  <https://github.com/cujojs/when/blob/master/docs/api.md#debugging-promises>`_.

- All of Mopidy.js' promise rejection values are now of the Error type. This
  ensures that all JavaScript VMs will show a useful stack trace if a rejected
  promise's value is used to throw an exception. To allow catch clauses to
  handle different errors differently, server side errors are of the type
  ``Mopidy.ServerError``, and connection related errors are of the type
  ``Mopidy.ConnectionError``.

- Add support for method calls with by-name arguments. The old calling
  convention, ``by-position-only``, is still the default, but this will
  change in the future. A warning is logged to the console if you don't
  explicitly select a calling convention. See the :ref:`mopidy-js` docs for
  details.

**MPD frontend**

- Proper command tokenization for MPD requests. This replaces the old regex
  based system with an MPD protocol specific tokenizer responsible for breaking
  requests into pieces before the handlers have at them.
  (Fixes: :issue:`591` and :issue:`592`)

- Updated command handler system. As part of the tokenizer cleanup we've
  updated how commands are registered and making it simpler to create new
  handlers.

- Simplified a bunch of handlers. All the "browse" type commands now use a
  common browse helper under the hood for less repetition. Likewise the query
  handling of "search" commands has been somewhat simplified.

- Adds placeholders for missing MPD commands, preparing the way for bumping the
  protocol version once they have been added.

- Respond to all pending requests before closing connection. (PR: :issue:`722`)

- Stop incorrectly catching `LookupError` in command handling.
  (Fixes: :issue:`741`)

- Browse support for playlists and albums has been added. (PR: :issue:`749`,
  :issue:`754`)

- The ``lsinfo`` command now returns browse results before local playlists.
  This is helpful as not all clients sort the returned items. (PR:
  :issue:`755`)

- Browse now supports different entries with identical names. (PR:
  :issue:`762`)

- Search terms that are empty or consists of only whitespace are no longer
  included in the search query sent to backends. (PR: :issue:`758`)

**Local backend**

- The JSON local library backend now logs a friendly message telling you about
  ``mopidy local scan`` if you don't have a local library cache. (Fixes:
  :issue:`711`)

- The ``local scan`` command now use multiple threads to walk the file system
  and check files' modification time. This speeds up scanning, escpecially
  when scanning remote file systems over e.g. NFS.

- the ``local scan`` command now creates necessary folders if they don't
  already exist. Previously, this was only done by the Mopidy server, so doing
  a ``local scan`` before running the server the first time resulted in a
  crash. (Fixes: :issue:`703`)

- Fix proper decoding of exception messages that depends on the user's locale.

**Stream backend**

- Add config value :confval:`stream/metadata_blacklist` to blacklist certain
  URIs we should not open to read metadata from before they are opened for
  playback. This is typically needed for services that invalidate URIs after a
  single use. (Fixes: :issue:`660`)


v0.18.3 (2014-02-16)
====================

Bug fix release.

- Fix documentation build.


v0.18.2 (2014-02-16)
====================

Bug fix release.

- We now log warnings for wrongly configured extensions, and clearly label them
  in ``mopidy config``, but does no longer stop Mopidy from starting because of
  misconfigured extensions. (Fixes: :issue:`682`)

- Fix a crash in the server side WebSocket handler caused by connection
  problems with clients. (Fixes: :issue:`428`, :issue:`571`)

- Fix the ``time_position`` field of the ``track_playback_ended`` event, which
  has been always 0 since v0.18.0. This made scrobbles by Mopidy-Scrobbler not
  be persisted by Last.fm, because Mopidy reported that you listened to 0
  seconds of each track. (Fixes: :issue:`674`)

- Fix the log setup so that it is possible to increase the amount of logging
  from a specific logger using the ``loglevels`` config section. (Fixes:
  :issue:`684`)

- Serialization of :class:`~mopidy.models.Playlist` models with the
  ``last_modified`` field set to a :class:`datetime.datetime` instance did not
  work. The type of :attr:`mopidy.models.Playlist.last_modified` has been
  redefined from a :class:`datetime.datetime` instance to the number of
  milliseconds since Unix epoch as an integer. This makes serialization of the
  time stamp simpler.

- Minor refactor of the MPD server context so that Mopidy's MPD protocol
  implementation can easier be reused. (Fixes: :issue:`646`)

- Network and signal handling has been updated to play nice on Windows systems.


v0.18.1 (2014-01-23)
====================

Bug fix release.

- Disable extension instead of crashing if a dependency has the wrong
  version. (Fixes: :issue:`657`)

- Make logging work to both console, debug log file, and any custom logging
  setup from :confval:`logging/config_file` at the same time. (Fixes:
  :issue:`661`)


v0.18.0 (2014-01-19)
====================

The focus of 0.18 have been on two fronts: the local library and browsing.

First, the local library's old tag cache file used for storing the track
metadata scanned from your music collection has been replaced with a far
simpler implementation using JSON as the storage format. At the same time, the
local library have been made replaceable by extensions, so you can now create
extensions that use your favorite database to store the metadata.

Second, we've finally implemented the long awaited "file system" browsing
feature that you know from MPD. It is supported by both the MPD frontend and
the local and Spotify backends. It is also used by the new Mopidy-Dirble
extension to provide you with a directory of Internet radio stations from all
over the world.

Since the release of 0.17, we've closed or merged 49 issues and pull requests
through about 285 commits by :ref:`11 people <authors>`, including six new
guys. Thanks to everyone that has contributed!

**Core API**

- Add :meth:`mopidy.core.Core.version` for HTTP clients to manage compatibility
  between API versions. (Fixes: :issue:`597`)

- Add :class:`mopidy.models.Ref` class for use as a lightweight reference to
  other model types, containing just an URI, a name, and an object type. It is
  barely used for now, but its use will be extended over time.

- Add :meth:`mopidy.core.LibraryController.browse` method for browsing a
  virtual file system of tracks. Backends can implement support for this by
  implementing :meth:`mopidy.backend.LibraryProvider.browse`.

- Events emitted on play/stop, pause/resume, next/previous and on end of track
  has been cleaned up to work consistently. See the message of
  :commit:`1d108752f6` for the full details. (Fixes: :issue:`629`)

**Backend API**

- Move the backend API classes from :mod:`mopidy.backends.base` to
  :mod:`mopidy.backend` and remove the ``Base`` prefix from the class names:

  - From :class:`mopidy.backends.base.Backend`
    to :class:`mopidy.backend.Backend`

  - From :class:`mopidy.backends.base.BaseLibraryProvider`
    to :class:`mopidy.backend.LibraryProvider`

  - From :class:`mopidy.backends.base.BasePlaybackProvider`
    to :class:`mopidy.backend.PlaybackProvider`

  - From :class:`mopidy.backends.base.BasePlaylistsProvider`
    to :class:`mopidy.backend.PlaylistsProvider`

  - From :class:`mopidy.backends.listener.BackendListener`
    to :class:`mopidy.backend.BackendListener`

  Imports from the old locations still works, but are deprecated.

- Add :meth:`mopidy.backend.LibraryProvider.browse`, which can be implemented
  by backends that wants to expose directories of tracks in Mopidy's virtual
  file system.

**Frontend API**

- The dummy backend used for testing many frontends have moved from
  :mod:`mopidy.backends.dummy` to :mod:`mopidy.backend.dummy`.
  (PR: :issue:`984`)

**Commands**

- Reduce amount of logging from dependencies when using :option:`mopidy -v`.
  (Fixes: :issue:`593`)

- Add support for additional logging verbosity levels with ``mopidy -vv`` and
  ``mopidy -vvv`` which increases the amount of logging from dependencies.
  (Fixes: :issue:`593`)

**Configuration**

- The default for the :option:`mopidy --config` option has been updated to
  include ``$XDG_CONFIG_DIRS`` in addition to ``$XDG_CONFIG_DIR``. (Fixes
  :issue:`431`)

- Added support for deprecating config values in order to allow for graceful
  removal of the no longer used config value :confval:`local/tag_cache_file`.

**Extension support**

- Switched to using a registry model for classes provided by extension. This
  allows extensions to be extended by other extensions, as needed by for
  example pluggable libraries for the local backend. See
  :class:`mopidy.ext.Registry` for details. (Fixes :issue:`601`)

- Added the new method :meth:`mopidy.ext.Extension.setup`. This method
  replaces the now deprecated
  :meth:`~mopidy.ext.Extension.get_backend_classes`,
  :meth:`~mopidy.ext.Extension.get_frontend_classes`, and
  :meth:`~mopidy.ext.Extension.register_gstreamer_elements`.

**Audio**

- Added :confval:`audio/mixer_volume` to set the initial volume of mixers.
  This is especially useful for setting the software mixer volume to something
  else than the default 100%. (Fixes: :issue:`633`)

**Local backend**

.. note::

    After upgrading to Mopidy 0.18 you must run ``mopidy local scan`` to
    reindex your local music collection. This is due to the change of storage
    format.

- Added support for browsing local directories in Mopidy's virtual file system.

- Finished the work on creating pluggable libraries. Users can now
  reconfigure Mopidy to use alternate library providers of their choosing for
  local files. (Fixes issue :issue:`44`, partially resolves :issue:`397`, and
  causes a temporary regression of :issue:`527`.)

- Switched default local library provider from a "tag cache" file that closely
  resembled the one used by the original MPD server to a compressed JSON file.
  This greatly simplifies our library code and reuses our existing model
  serialization code, as used by the HTTP API and web clients.

- Removed our outdated and bug-ridden "tag cache" local library implementation.

- Added the config value :confval:`local/library` to select which library to
  use. It defaults to ``json``, which is the only local library bundled with
  Mopidy.

- Added the config value :confval:`local/data_dir` to have a common config for
  where to store local library data. This is intended to avoid every single
  local library provider having to have it's own config value for this.

- Added the config value :confval:`local/scan_flush_threshold` to control how
  often to tell local libraries to store changes when scanning local music.

**Streaming backend**

- Add live lookup of URI metadata. (Fixes :issue:`540`)

- Add support for extended M3U playlist, meaning that basic track metadata
  stored in playlists will be used by Mopidy.

**HTTP frontend**

- Upgrade Mopidy.js dependencies and add support for using Mopidy.js with
  Browserify. This version has been released to npm as Mopidy.js v0.2.0.
  (Fixes: :issue:`609`)

**MPD frontend**

- Make the ``lsinfo``, ``listall``, and ``listallinfo`` commands support
  browsing of Mopidy's virtual file system. (Fixes: :issue:`145`)

- Empty commands now return a ``ACK [5@0] {} No command given`` error instead
  of ``OK``. This is consistent with the original MPD server implementation.

**Internal changes**

- Events from the audio actor, backends, and core actor are now emitted
  asyncronously through the GObject event loop. This should resolve the issue
  that has blocked the merge of the EOT-vs-EOS fix for a long time.


v0.17.0 (2013-11-23)
====================

The focus of 0.17 has been on introducing subcommands to the ``mopidy``
command, making it possible for extensions to add subcommands of their own, and
to improve the default config file when starting Mopidy the first time. In
addition, we've grown support for Zeroconf publishing of the MPD and HTTP
servers, and gotten a much faster scanner. The scanner now also scans some
additional tags like composers and performers.

Since the release of 0.16, we've closed or merged 22 issues and pull requests
through about 200 commits by :ref:`five people <authors>`, including one new
contributor.

**Commands**

- Switched to subcommands for the ``mopidy`` command , this implies the
  following changes: (Fixes: :issue:`437`)

  ===================== =================
  Old command           New command
  ===================== =================
  mopidy --show-deps    mopidy deps
  mopidy --show-config  mopidy config
  mopidy-scan           mopidy local scan
  ===================== =================

- Added hooks for extensions to create their own custom subcommands and
  converted ``mopidy-scan`` as a first user of the new API. (Fixes:
  :issue:`436`)

**Configuration**

- When ``mopidy`` is started for the first time we create an empty
  :file:`{$XDG_CONFIG_DIR}/mopidy/mopidy.conf` file. We now populate this file
  with the default config for all installed extensions so it'll be easier to
  set up Mopidy without looking through all the documentation for relevant
  config values. (Fixes: :issue:`467`)

**Core API**

- The :class:`~mopidy.models.Track` model has grown fields for ``composers``,
  ``performers``, ``genre``, and ``comment``.

- The search field ``track`` has been renamed to ``track_name`` to avoid
  confusion with ``track_no``. (Fixes: :issue:`535`)

- The signature of the tracklist's
  :meth:`~mopidy.core.TracklistController.filter` and
  :meth:`~mopidy.core.TracklistController.remove` methods have changed.
  Previously, they expected e.g. ``tracklist.filter(tlid=17)``. Now, the value
  must always be a list, e.g. ``tracklist.filter(tlid=[17])``. This change
  allows you to get or remove multiple tracks with a single call, e.g.
  ``tracklist.remove(tlid=[1, 2, 7])``. This is especially useful for web
  clients, as requests can be batched. This also brings the interface closer to
  the library's :meth:`~mopidy.core.LibraryController.find_exact` and
  :meth:`~mopidy.core.LibraryController.search` methods.

**Audio**

- Change default volume mixer from ``autoaudiomixer`` to ``software``.
  GStreamer 1.x does not support volume control, so we're changing to use
  software mixing by default, as that may be the only thing we'll support in
  the future when we upgrade to GStreamer 1.x.

**Local backend**

- Library scanning has been switched back from GStreamer's discoverer to our
  custom implementation due to various issues with GStreamer 0.10's built in
  scanner. This also fixes the scanner slowdown. (Fixes: :issue:`565`)

- When scanning, we no longer default the album artist to be the same as the
  track artist. Album artist is now only populated if the scanned file got an
  explicit album artist set.

- The scanner will now extract multiple artists from files with multiple artist
  tags.

- The scanner will now extract composers and performers, as well as genre,
  bitrate, and comments. (Fixes: :issue:`577`)

- Fix scanner so that time of last modification is respected when deciding
  which files can be skipped when scanning the music collection for changes.

- The scanner now ignores the capitalization of file extensions in
  :confval:`local/excluded_file_extensions`, so you no longer need to list both
  ``.jpg`` and ``.JPG`` to ignore JPEG files when scanning. (Fixes:
  :issue:`525`)

- The scanner now by default ignores ``*.nfo`` and ``*.html`` files too.

**MPD frontend**

- The MPD service is now published as a Zeroconf service if avahi-daemon is
  running on the system. Some MPD clients will use this to present Mopidy as an
  available server on the local network without needing any configuration. See
  the :confval:`mpd/zeroconf` config value to change the service name or
  disable the service. (Fixes: :issue:`39`)

- Add support for ``composer``, ``performer``, ``comment``, ``genre``, and
  ``performer``.  These tags can be used with ``list ...``, ``search ...``, and
  ``find ...`` and their variants, and are supported in the ``any`` tag also

- The ``bitrate`` field in the ``status`` response is now always an integer.
  This follows the behavior of the original MPD server. (Fixes: :issue:`577`)

**HTTP frontend**

- The HTTP service is now published as a Zeroconf service if avahi-daemon is
  running on the system. Some browsers will present HTTP Zeroconf services on
  the local network as "local sites" bookmarks. See the
  :confval:`http/zeroconf` config value to change the service name or disable
  the service. (Fixes: :issue:`39`)

**DBUS/MPRIS**

- The ``mopidy`` process now registers it's GObject event loop as the default
  eventloop for dbus-python. (Fixes: :mpris:`2`)


v0.16.1 (2013-11-02)
====================

This is very small release to get Mopidy's Debian package ready for inclusion
in Debian.

**Commands**

- Fix removal of last dir level in paths to dependencies in
  ``mopidy --show-deps`` output.

- Add manpages for all commands.

**Local backend**

- Fix search filtering by track number that was added in 0.16.0.

**MPD frontend**

- Add support for ``list "albumartist" ...`` which was missed when ``find`` and
  ``search`` learned to handle ``albumartist`` in 0.16.0. (Fixes: :issue:`553`)


v0.16.0 (2013-10-27)
====================

The goals for 0.16 were to add support for queuing playlists of e.g. radio
streams directly to Mopidy, without manually extracting the stream URLs from
the playlist first, and to move the Spotify, Last.fm, and MPRIS support out to
independent Mopidy extensions, living outside the main Mopidy repo. In
addition, we've seen some cleanup to the playback vs tracklist part of the core
API, which will require some changes for users of the HTTP/JavaScript APIs, as
well as the addition of audio muting to the core API. To speed up the
:ref:`development of new extensions <extensiondev>`, we've added a cookiecutter
project to get the skeleton of a Mopidy extension up and running in a matter of
minutes. Read below for all the details and for links to issues with even more
details.

Since the release of 0.15, we've closed or merged 31 issues and pull requests
through about 200 commits by :ref:`five people <authors>`, including three new
contributors.

**Dependencies**

Parts of Mopidy have been moved to their own external extensions. If you want
Mopidy to continue to work like it used to, you may have to install one or more
of the following extensions as well:

- The Spotify backend has been moved to
  `Mopidy-Spotify <https://github.com/mopidy/mopidy-spotify>`_.

- The Last.fm scrobbler has been moved to
  `Mopidy-Scrobbler <https://github.com/mopidy/mopidy-scrobbler>`_.

- The MPRIS frontend has been moved to
  `Mopidy-MPRIS <https://github.com/mopidy/mopidy-mpris>`_.

**Core**

- Parts of the functionality in :class:`mopidy.core.PlaybackController` have
  been moved to :class:`mopidy.core.TracklistController`:

  =================================== ==================================
  Old location                        New location
  =================================== ==================================
  playback.get_consume()              tracklist.get_consume()
  playback.set_consume(v)             tracklist.set_consume(v)
  playback.consume                    tracklist.consume

  playback.get_random()               tracklist.get_random()
  playback.set_random(v)              tracklist.set_random(v)
  playback.random                     tracklist.random

  playback.get_repeat()               tracklist.get_repeat()
  playback.set_repeat(v)              tracklist.set_repeat(v)
  playback.repeat                     tracklist.repeat

  playback.get_single()               tracklist.get_single()
  playback.set_single(v)              tracklist.set_single(v)
  playback.single                     tracklist.single

  playback.get_tracklist_position()   tracklist.index(tl_track)
  playback.tracklist_position         tracklist.index(tl_track)

  playback.get_tl_track_at_eot()      tracklist.eot_track(tl_track)
  playback.tl_track_at_eot            tracklist.eot_track(tl_track)

  playback.get_tl_track_at_next()     tracklist.next_track(tl_track)
  playback.tl_track_at_next           tracklist.next_track(tl_track)

  playback.get_tl_track_at_previous() tracklist.previous_track(tl_track)
  playback.tl_track_at_previous       tracklist.previous_track(tl_track)
  =================================== ==================================

  The ``tl_track`` argument to the last four new functions are used as the
  reference ``tl_track`` in the tracklist to find e.g. the next track. Usually,
  this will be :attr:`~mopidy.core.PlaybackController.current_tl_track`.

- Added :attr:`mopidy.core.PlaybackController.mute` for muting and unmuting
  audio. (Fixes: :issue:`186`)

- Added :meth:`mopidy.core.CoreListener.mute_changed` event that is triggered
  when the mute state changes.

- In "random" mode, after a full playthrough of the tracklist, playback
  continued from the last track played to the end of the playlist in non-random
  order. It now stops when all tracks have been played once, unless "repeat"
  mode is enabled. (Fixes: :issue:`453`)

- In "single" mode, after a track ended, playback continued with the next track
  in the tracklist. It now stops after playing a single track, unless "repeat"
  mode is enabled. (Fixes: :issue:`496`)

**Audio**

- Added support for parsing and playback of playlists in GStreamer.  For end
  users this basically means that you can now add a radio playlist to Mopidy
  and we will automatically download it and play the stream inside it.
  Currently we support M3U, PLS, XSPF and ASX files. Also note that we can
  currently only play the first stream in the playlist.

- We now handle the rare case where an audio track has max volume equal to min.
  This was causing divide by zero errors when scaling volumes to a zero to
  hundred scale. (Fixes: :issue:`525`)

- Added support for muting audio without setting the volume to 0. This works
  both for the software and hardware mixers. (Fixes: :issue:`186`)

**Local backend**

- Replaced our custom media library scanner with GStreamer's builtin scanner.
  This should make scanning less error prone and faster as timeouts should be
  infrequent. (Fixes: :issue:`198`)

- Media files with less than 100ms duration are now excluded from the library.

- Media files with the file extensions ``.jpeg``, ``.jpg``, ``.png``, ``.txt``,
  and ``.log`` are now skipped by the media library scanner. You can change the
  list of excluded file extensions by setting the
  :confval:`local/excluded_file_extensions` config value. (Fixes: :issue:`516`)

- Unknown URIs found in playlists are now made into track objects with the URI
  set instead of being ignored. This makes it possible to have playlists with
  e.g. HTTP radio streams and not just ``local:track:...`` URIs. This used to
  work, but was broken in Mopidy 0.15.0. (Fixes: :issue:`527`)

- Fixed crash when playing ``local:track:...`` URIs which contained non-ASCII
  chars after uridecode.

- Removed media files are now also removed from the in-memory media library
  when the media library is reloaded from disk. (Fixes: :issue:`500`)

**MPD frontend**

- Made the formerly unused commands ``outputs``, ``enableoutput``, and
  ``disableoutput`` mute/unmute audio. (Related to: :issue:`186`)

- The MPD command ``list`` now works with ``"albumartist"`` as its second
  argument, e.g. ``list "album" "albumartist" "anartist"``. (Fixes:
  :issue:`468`)

- The MPD commands ``find`` and ``search`` now accepts ``albumartist`` and
  ``track`` (this is the track number, not the track name) as field types to
  limit the search result with.

- The MPD command ``count`` is now implemented. It accepts the same type of
  arguments as ``find`` and ``search``, but returns the number of tracks and
  their total playtime instead.

**Extension support**

- A cookiecutter project for quickly creating new Mopidy extensions have been
  created. You can find it at `cookiecutter-mopidy-ext
  <https://github.com/mopidy/cookiecutter-mopidy-ext>`_. (Fixes: :issue:`522`)


v0.15.0 (2013-09-19)
====================

A release with a number of small and medium fixes, with no specific focus.

**Dependencies**

- Mopidy no longer supports Python 2.6. Currently, the only Python version
  supported by Mopidy is Python 2.7. We're continuously working towards running
  Mopidy on Python 3. (Fixes: :issue:`344`)

**Command line options**

- Converted from the optparse to the argparse library for handling command line
  options.

- ``mopidy --show-config`` will now take into consideration any
  :option:`mopidy --option` arguments appearing later on the command line. This
  helps you see the effective configuration for runs with the same
  ``mopidy --options`` arguments.

**Audio**

- Added support for audio visualization. :confval:`audio/visualizer` can now be
  set to GStreamer visualizers.

- Properly encode localized mixer names before logging.

**Local backend**

- An album's number of discs and a track's disc number are now extracted when
  scanning your music collection.

- The scanner now gives up scanning a file after a second, and continues with
  the next file. This fixes some hangs on non-media files, like logs. (Fixes:
  :issue:`476`, :issue:`483`)

- Added support for pluggable library updaters. This allows extension writers
  to start providing their own custom libraries instead of being stuck with
  just our tag cache as the only option.

- Converted local backend to use new ``local:playlist:path`` and
  ``local:track:path`` URI scheme. Also moves support of ``file://`` to
  streaming backend.

**Spotify backend**

- Prepend playlist folder names to the playlist name, so that the playlist
  hierarchy from your Spotify account is available in Mopidy. (Fixes:
  :issue:`62`)

- Fix proxy config values that was broken with the config system change in
  0.14. (Fixes: :issue:`472`)

**MPD frontend**

- Replace newline, carriage return and forward slash in playlist names. (Fixes:
  :issue:`474`, :issue:`480`)

- Accept ``listall`` and ``listallinfo`` commands without the URI parameter.
  The methods are still not implemented, but now the commands are accepted as
  valid.

**HTTP frontend**

- Fix too broad truth test that caused :class:`mopidy.models.TlTrack`
  objects with ``tlid`` set to ``0`` to be sent to the HTTP client without the
  ``tlid`` field. (Fixes: :issue:`501`)

- Upgrade Mopidy.js dependencies. This version has been released to npm as
  Mopidy.js v0.1.1.

**Extension support**

- :class:`mopidy.config.Secret` is now deserialized to unicode instead of
  bytes. This may require modifications to extensions.


v0.14.2 (2013-07-01)
====================

This is a maintenance release to make Mopidy 0.14 work with pyspotify 1.11.

**Dependencies**

- pyspotify >= 1.9, < 2 is now required for Spotify support. In other words,
  you're free to upgrade to pyspotify 1.11, but it isn't a requirement.


v0.14.1 (2013-04-28)
====================

This release addresses an issue in v0.14.0 where the new
``mopidy-convert-config`` tool and the new :option:`mopidy --option`
command line option was broken because some string operations inadvertently
converted some byte strings to unicode.


v0.14.0 (2013-04-28)
====================

The 0.14 release has a clear focus on two things: the new configuration system
and extension support. Mopidy's documentation has also been greatly extended
and improved.

Since the last release a month ago, we've closed or merged 53 issues and pull
requests. A total of seven :ref:`authors <authors>` have contributed, including
one new.

**Dependencies**

- setuptools or distribute is now required. We've introduced this dependency to
  use setuptools' entry points functionality to find installed Mopidy
  extensions.

**New configuration system**

- Mopidy has a new configuration system based on ini-style files instead of a
  Python file. This makes configuration easier for users, and also makes it
  possible for Mopidy extensions to have their own config sections.

  As part of this change we have cleaned up the naming of our config values.

  To ease migration we've made a tool named ``mopidy-convert-config`` for
  automatically converting the old ``settings.py`` to a new ``mopidy.conf``
  file. This tool takes care of all the renamed config values as well. See
  ``mopidy-convert-config`` for details on how to use it.

- A long wanted feature: You can now enable or disable specific frontends or
  backends without having to redefine :attr:`~mopidy.settings.FRONTENDS` or
  :attr:`~mopidy.settings.BACKENDS` in your config. Those config values are
  gone completely.

**Extension support**

- Mopidy now supports extensions. This means that any developer now easily can
  create a Mopidy extension to add new control interfaces or music backends.
  This helps spread the maintenance burden across more developers, and also
  makes it possible to extend Mopidy with new backends the core developers are
  unable to create and/or maintain because of geo restrictions, etc. If you're
  interested in creating an extension for Mopidy, read up on
  :ref:`extensiondev`.

- All of Mopidy's existing frontends and backends are now plugged into Mopidy
  as extensions, but they are still distributed together with Mopidy and are
  enabled by default.

- The NAD mixer have been moved out of Mopidy core to its own project,
  Mopidy-NAD. See :ref:`ext` for more information.

- Janez Troha has made the first two external extensions for Mopidy: a backend
  for playing music from Soundcloud, and a backend for playing music from a
  Beets music library. See :ref:`ext` for more information.

**Command line options**

- The command option ``mopidy --list-settings`` is now named
  ``mopidy --show-config``.

- The command option ``mopidy --list-deps`` is now named
  ``mopidy --show-deps``.

- What configuration files to use can now be specified through the command
  option :option:`mopidy --config`, multiple files can be specified using colon
  as a separator.

- Configuration values can now be overridden through the command option
  :option:`mopidy --option`. For example: ``mopidy --option
  spotify/enabled=false``.

- The GStreamer command line options, ``mopidy --gst-*`` and
  ``mopidy --help-gst`` are no longer supported. To set GStreamer debug
  flags, you can use environment variables such as :envvar:`GST_DEBUG`. Refer
  to GStreamer's documentation for details.

**Spotify backend**

- Add support for starred playlists, both your own and those owned by other
  users. (Fixes: :issue:`326`)

- Fix crash when a new playlist is added by another Spotify client. (Fixes:
  :issue:`387`, :issue:`425`)

**MPD frontend**

- Playlists with identical names are now handled properly by the MPD frontend
  by suffixing the duplicate names with e.g. ``[2]``. This is needed because
  MPD identify playlists by name only, while Mopidy and Spotify supports
  multiple playlists with the same name, and identify them using an URI.
  (Fixes: :issue:`114`)

**MPRIS frontend**

- The frontend is now disabled if the :envvar:`DISPLAY` environment variable is
  unset. This avoids some harmless error messages, that have been known to
  confuse new users debugging other problems.

**Development**

- Developers running Mopidy from a Git clone now need to run ``python setup.py
  develop`` to register the bundled extensions. If you don't do this, Mopidy
  will not find any frontends or backends. Note that we highly recomend you do
  this in a virtualenv, not system wide. As a bonus, the command also gives
  you a ``mopidy`` executable in your search path.


v0.13.0 (2013-03-31)
====================

The 0.13 release brings small improvements and bugfixes throughout Mopidy.
There are no major new features, just incremental improvement of what we
already have.

**Dependencies**

- Pykka >= 1.1 is now required.

**Core**

- Removed the :attr:`mopidy.settings.DEBUG_THREAD` setting and the
  ``mopidy --debug-thread`` command line option. Sending SIGUSR1 to
  the Mopidy process will now always make it log tracebacks for all alive
  threads.

- Log a warning if a track isn't playable to make it more obvious that backend
  X needs backend Y to be present for playback to work.

- :meth:`mopidy.core.TracklistController.add` now accepts an ``uri`` which it
  will lookup in the library and then add to the tracklist. This is helpful
  for e.g. web clients that doesn't want to transfer all track meta data back
  to the server just to add it to the tracklist when the server already got all
  the needed information easily available. (Fixes: :issue:`325`)

- Change the following methods to accept an ``uris`` keyword argument:

  - :meth:`mopidy.core.LibraryController.find_exact`
  - :meth:`mopidy.core.LibraryController.search`

  Search queries will only be forwarded to backends handling the given URI
  roots, and the backends may use the URI roots to further limit what results
  are returned. For example, a search with ``uris=['file:']`` will only be
  processed by the local backend. A search with
  ``uris=['file:///media/music']`` will only be processed by the local backend,
  and, if such filtering is supported by the backend, will only return results
  with URIs within the given URI root.

**Audio sub-system**

- Make audio error logging handle log messages with non-ASCII chars. (Fixes:
  :issue:`347`)

**Local backend**

- Make ``mopidy-scan`` work with Ogg Vorbis files. (Fixes: :issue:`275`)

- Fix playback of files with non-ASCII chars in their file path. (Fixes:
  :issue:`353`)

**Spotify backend**

- Let GStreamer handle time position tracking and seeks. (Fixes: :issue:`191`)

- For all playlists owned by other Spotify users, we now append the owner's
  username to the playlist name. (Partly fixes: :issue:`114`)

**HTTP frontend**

- Mopidy.js now works both from browsers and from Node.js environments. This
  means that you now can make Mopidy clients in Node.js. Mopidy.js has been
  published to the `npm registry <https://www.npmjs.com/package/mopidy>`_ for easy
  installation in Node.js projects.

- Upgrade Mopidy.js' build system Grunt from 0.3 to 0.4.

- Upgrade Mopidy.js' dependencies when.js from 1.6.1 to 2.0.0.

- Expose :meth:`mopidy.core.Core.get_uri_schemes` to HTTP clients. It is
  available through Mopidy.js as ``mopidy.getUriSchemes()``.

**MPRIS frontend**

- Publish album art URIs if available.

- Publish disc number of track if available.


v0.12.0 (2013-03-12)
====================

The 0.12 release has been delayed for a while because of some issues related
some ongoing GStreamer cleanup we didn't invest enough time to finish. Finally,
we've come to our senses and have now cherry-picked the good parts to bring you
a new release, while postponing the GStreamer changes to 0.13. The release adds
a new backend for playing audio streams, as well as various minor improvements
throughout Mopidy.

- Make Mopidy work on early Python 2.6 versions. (Fixes: :issue:`302`)

  - ``optparse`` fails if the first argument to ``add_option`` is a unicode
    string on Python < 2.6.2rc1.

  - ``foo(**data)`` fails if the keys in ``data`` is unicode strings on Python
    < 2.6.5rc1.

**Audio sub-system**

- Improve selection of mixer tracks for volume control. (Fixes: :issue:`307`)

**Local backend**

- Make ``mopidy-scan`` support symlinks.

**Stream backend**

We've added a new backend for playing audio streams, the :mod:`stream backend
<mopidy.stream>`. It is activated by default. The stream backend supports the
intersection of what your GStreamer installation supports and what protocols
are included in the :attr:`mopidy.settings.STREAM_PROTOCOLS` setting.

Current limitations:

- No metadata about the current track in the stream is available.

- Playlists are not parsed, so you can't play e.g. a M3U or PLS file which
  contains stream URIs. You need to extract the stream URL from the playlist
  yourself. See :issue:`303` for progress on this.

**Core API**

- :meth:`mopidy.core.PlaylistsController.get_playlists` now accepts an argument
  ``include_tracks``. This defaults to :class:`True`, which has the same old
  behavior. If set to :class:`False`, the tracks are stripped from the
  playlists before they are returned. This can be used to limit the amount of
  data returned if the response is to be passed out of the application, e.g. to
  a web client. (Fixes: :issue:`297`)

**Models**

- Add :attr:`mopidy.models.Album.images` field for including album art URIs.
  (Partly fixes :issue:`263`)

- Add :attr:`mopidy.models.Track.disc_no` field. (Partly fixes: :issue:`286`)

- Add :attr:`mopidy.models.Album.num_discs` field. (Partly fixes: :issue:`286`)


v0.11.1 (2012-12-24)
====================

Spotify search was broken in 0.11.0 for users of Python 2.6. This release fixes
it. If you're using Python 2.7, v0.11.0 and v0.11.1 should be equivalent.


v0.11.0 (2012-12-24)
====================

In celebration of Mopidy's three year anniversary December 23, we're releasing
Mopidy 0.11. This release brings several improvements, most notably better
search which now includes matching artists and albums from Spotify in the
search results.

**Settings**

- The settings validator now complains if a setting which expects a tuple of
  values (e.g. :attr:`mopidy.settings.BACKENDS`,
  :attr:`mopidy.settings.FRONTENDS`) has a non-iterable value. This typically
  happens because the setting value contains a single value and one has
  forgotten to add a comma after the string, making the value a tuple. (Fixes:
  :issue:`278`)

**Spotify backend**

- Add :attr:`mopidy.settings.SPOTIFY_TIMEOUT` setting which allows you to
  control how long we should wait before giving up on Spotify searches, etc.

- Add support for looking up albums, artists, and playlists by URI in addition
  to tracks. (Fixes: :issue:`67`)

  As an example of how this can be used, you can try the the following MPD
  commands which now all adds one or more tracks to your tracklist::

      add "spotify:track:1mwt9hzaH7idmC5UCoOUkz"
      add "spotify:album:3gpHG5MGwnipnap32lFYvI"
      add "spotify:artist:5TgQ66WuWkoQ2xYxaSTnVP"
      add "spotify:user:p3.no:playlist:0XX6tamRiqEgh3t6FPFEkw"

- Increase max number of tracks returned by searches from 100 to 200, which
  seems to be Spotify's current max limit.

**Local backend**

- Load track dates from tag cache.

- Add support for searching by track date.

**MPD frontend**

- Add :attr:`mopidy.settings.MPD_SERVER_CONNECTION_TIMEOUT` setting which
  controls how long an MPD client can stay inactive before the connection is
  closed by the server.

- Add support for the ``findadd`` command.

- Updated to match the MPD 0.17 protocol (Fixes: :issue:`228`):

  - Add support for ``seekcur`` command.

  - Add support for ``config`` command.

  - Add support for loading a range of tracks from a playlist to the ``load``
    command.

  - Add support for ``searchadd`` command.

  - Add support for ``searchaddpl`` command.

  - Add empty stubs for channel commands for client to client communication.

- Add support for search by date.

- Make ``seek`` and ``seekid`` not restart the current track before seeking in
  it.

- Include fake tracks representing albums and artists in the search results.
  When these are added to the tracklist, they expand to either all tracks in
  the album or all tracks by the artist. This makes it easy to play full albums
  in proper order, which is a feature that have been frequently requested.
  (Fixes: :issue:`67`, :issue:`148`)

**Internal changes**

*Models:*

- Specified that :attr:`mopidy.models.Playlist.last_modified` should be in UTC.

- Added :class:`mopidy.models.SearchResult` model to encapsulate search results
  consisting of more than just tracks.

*Core API:*

- Change the following methods to return :class:`mopidy.models.SearchResult`
  objects which can include both track results and other results:

  - :meth:`mopidy.core.LibraryController.find_exact`
  - :meth:`mopidy.core.LibraryController.search`

- Change the following methods to accept either a dict with filters or kwargs.
  Previously they only accepted kwargs, which made them impossible to use from
  the Mopidy.js through JSON-RPC, which doesn't support kwargs.

  - :meth:`mopidy.core.LibraryController.find_exact`
  - :meth:`mopidy.core.LibraryController.search`
  - :meth:`mopidy.core.PlaylistsController.filter`
  - :meth:`mopidy.core.TracklistController.filter`
  - :meth:`mopidy.core.TracklistController.remove`

- Actually trigger the :meth:`mopidy.core.CoreListener.volume_changed` event.

- Include the new volume level in the
  :meth:`mopidy.core.CoreListener.volume_changed` event.

- The ``track_playback_{paused,resumed,started,ended}`` events now include a
  :class:`mopidy.models.TlTrack` instead of a :class:`mopidy.models.Track`.

*Audio:*

- Mixers with fewer than 100 volume levels could report another volume level
  than what you just set due to the conversion between Mopidy's 0-100 range and
  the mixer's range. Now Mopidy returns the recently set volume if the mixer
  reports a volume level that matches the recently set volume, otherwise the
  mixer's volume level is rescaled to the 1-100 range and returned.


v0.10.0 (2012-12-12)
====================

We've added an HTTP frontend for those wanting to build web clients for Mopidy!

**Dependencies**

- pyspotify >= 1.9, < 1.11 is now required for Spotify support. In other words,
  you're free to upgrade to pyspotify 1.10, but it isn't a requirement.

**Documentation**

- Added installation instructions for Fedora.

**Spotify backend**

- Save a lot of memory by reusing artist, album, and track models.

- Make sure the playlist loading hack only runs once.

**Local backend**

- Change log level from error to warning on messages emitted when the tag cache
  isn't found and a couple of similar cases.

- Make ``mopidy-scan`` ignore invalid dates, e.g. dates in years outside the
  range 1-9999.

- Make ``mopidy-scan`` accept ``-q``/``--quiet`` and ``-v``/``--verbose``
  options to control the amount of logging output when scanning.

- The scanner can now handle files with other encodings than UTF-8. Rebuild
  your tag cache with ``mopidy-scan`` to include tracks that may have been
  ignored previously.

**HTTP frontend**

- Added new optional HTTP frontend which exposes Mopidy's core API through
  JSON-RPC 2.0 messages over a WebSocket. See :ref:`http-api` for further
  details.

- Added a JavaScript library, Mopidy.js, to make it easier to develop web based
  Mopidy clients using the new HTTP frontend.

**Bug fixes**

- :issue:`256`: Fix crash caused by non-ASCII characters in paths returned from
  ``glib``. The bug can be worked around by overriding the settings that
  includes offending ``$XDG_`` variables.


v0.9.0 (2012-11-21)
===================

Support for using the local and Spotify backends simultaneously have for a very
long time been our most requested feature. Finally, it's here!

**Dependencies**

- pyspotify >= 1.9, < 1.10 is now required for Spotify support.

**Documentation**

- New :ref:`installation` guides, organized by OS and distribution so that you
  can follow one concise list of instructions instead of jumping around the
  docs to look for instructions for each dependency.

- Moved :ref:`raspberrypi-installation` howto from the wiki to the docs.

- Updated :ref:`mpd-clients` overview.

- Added :ref:`mpris-clients` and :ref:`upnp-clients` overview.

**Multiple backends support**

- Both the local backend and the Spotify backend are now turned on by default.
  The local backend is listed first in the :attr:`mopidy.settings.BACKENDS`
  setting, and are thus given the highest priority in e.g. search results,
  meaning that we're listing search hits from the local backend first. If you
  want to prioritize the backends in another way, simply set ``BACKENDS`` in
  your own settings file and reorder the backends.

  There are no other setting changes related to the local and Spotify backends.
  As always, see :mod:`mopidy.settings` for the full list of available
  settings.

**Spotify backend**

- The Spotify backend now includes release year and artist on albums.

- :issue:`233`: The Spotify backend now returns the track if you search for the
  Spotify track URI.

- Added support for connecting to the Spotify service through an HTTP or SOCKS
  proxy, which is supported by pyspotify >= 1.9.

- Subscriptions to other Spotify user's "starred" playlists are ignored, as
  they currently isn't fully supported by pyspotify.

**Local backend**

- :issue:`236`: The ``mopidy-scan`` command failed to include tags from ALAC
  files (Apple lossless) because it didn't support multiple tag messages from
  GStreamer per track it scanned.

- Added support for search by filename to local backend.

**MPD frontend**

- :issue:`218`: The MPD commands ``listplaylist`` and ``listplaylistinfo`` now
  accepts unquoted playlist names if they don't contain spaces.

- :issue:`246`: The MPD command ``list album artist ""`` and similar
  ``search``, ``find``, and ``list`` commands with empty filter values caused a
  :exc:`LookupError`, but should have been ignored by the MPD server.

- The MPD frontend no longer lowercases search queries. This broke e.g. search
  by URI, where casing may be essential.

- The MPD command ``plchanges`` always returned the entire playlist. It now
  returns an empty response when the client has seen the latest version.

- The MPD commands ``search`` and ``find`` now allows the key ``file``, which
  is used by ncmpcpp instead of ``filename``.

- The MPD commands ``search`` and ``find`` now allow search query values to be
  empty strings.

- The MPD command ``listplaylists`` will no longer return playlists without a
  name. This could crash ncmpcpp.

- The MPD command ``list`` will no longer return artist names, album names, or
  dates that are blank.

- The MPD command ``decoders`` will now return an empty response instead of a
  "not implemented" error to make the ncmpcpp browse view work the first time
  it is opened.

**MPRIS frontend**

- The MPRIS playlists interface is now supported by our MPRIS frontend. This
  means that you now can select playlists to queue and play from the Ubuntu
  Sound Menu.

**Audio mixers**

- Made the :mod:`NAD mixer <mopidy.audio.mixers.nad>` responsive to interrupts
  during amplifier calibration. It will now quit immediately, while previously
  it completed the calibration first, and then quit, which could take more than
  15 seconds.

**Developer support**

- Added optional background thread for debugging deadlocks. When the feature is
  enabled via the ``mopidy --debug-thread`` option or
  :attr:`mopidy.settings.DEBUG_THREAD` setting a ``SIGUSR1`` signal will dump
  the traceback for all running threads.

- The settings validator will now allow any setting prefixed with ``CUSTOM_``
  to exist in the settings file.

**Internal changes**

Internally, Mopidy have seen a lot of changes to pave the way for multiple
backends and the future HTTP frontend.

- A new layer and actor, "core", has been added to our stack, inbetween the
  frontends and the backends. The responsibility of the core layer and actor is
  to take requests from the frontends, pass them on to one or more backends,
  and combining the response from the backends into a single response to the
  requesting frontend.

  Frontends no longer know anything about the backends. They just use the
  :ref:`core-api`.

- The dependency graph between the core controllers and the backend providers
  have been straightened out, so that we don't have any circular dependencies.
  The frontend, core, backend, and audio layers are now strictly separate. The
  frontend layer calls on the core layer, and the core layer calls on the
  backend layer. Both the core layer and the backends are allowed to call on
  the audio layer. Any data flow in the opposite direction is done by
  broadcasting of events to listeners, through e.g.
  :class:`mopidy.core.CoreListener` and :class:`mopidy.audio.AudioListener`.

  See :ref:`concepts` for more details and illustrations of all the relations.

- All dependencies are now explicitly passed to the constructors of the
  frontends, core, and the backends. This makes testing each layer with
  dummy/mocked lower layers easier than with the old variant, where
  dependencies where looked up in Pykka's actor registry.

- All properties in the core API now got getters, and setters if setting them
  is allowed. They are not explictly listed in the docs as they have the same
  behavior as the documented properties, but they are available and may be
  used. This is useful for the future HTTP frontend.

*Models:*

- Added :attr:`mopidy.models.Album.date` attribute. It has the same format as
  the existing :attr:`mopidy.models.Track.date`.

- Added :class:`mopidy.models.ModelJSONEncoder` and
  :func:`mopidy.models.model_json_decoder` for automatic JSON serialization and
  deserialization of data structures which contains Mopidy models. This is
  useful for the future HTTP frontend.

*Library:*

- :meth:`mopidy.core.LibraryController.find_exact` and
  :meth:`mopidy.core.LibraryController.search` now returns plain lists of
  tracks instead of playlist objects.

- :meth:`mopidy.core.LibraryController.lookup` now returns a list of tracks
  instead of a single track. This makes it possible to support lookup of
  artist or album URIs which then can expand to a list of tracks.

*Playback:*

- The base playback provider has been updated with sane default behavior
  instead of empty functions. By default, the playback provider now lets
  GStreamer keep track of the current track's time position. The local backend
  simply uses the base playback provider without any changes. Any future
  backend that just feeds URIs to GStreamer to play can also use the base
  playback provider without any changes.

- Removed :attr:`mopidy.core.PlaybackController.track_at_previous`. Use
  :attr:`mopidy.core.PlaybackController.tl_track_at_previous` instead.

- Removed :attr:`mopidy.core.PlaybackController.track_at_next`. Use
  :attr:`mopidy.core.PlaybackController.tl_track_at_next` instead.

- Removed :attr:`mopidy.core.PlaybackController.track_at_eot`. Use
  :attr:`mopidy.core.PlaybackController.tl_track_at_eot` instead.

- Removed :attr:`mopidy.core.PlaybackController.current_tlid`. Use
  :attr:`mopidy.core.PlaybackController.current_tl_track` instead.

*Playlists:*

The playlists part of the core API has been revised to be more focused around
the playlist URI, and some redundant functionality has been removed:

- Renamed "stored playlists" to "playlists" everywhere, including the core API
  used by frontends.

- :attr:`mopidy.core.PlaylistsController.playlists` no longer supports
  assignment to it. The `playlists` property on the backend layer still does,
  and all functionality is maintained by assigning to the playlists collections
  at the backend level.

- :meth:`mopidy.core.PlaylistsController.delete` now accepts an URI, and not a
  playlist object.

- :meth:`mopidy.core.PlaylistsController.save` now returns the saved playlist.
  The returned playlist may differ from the saved playlist, and should thus be
  used instead of the playlist passed to
  :meth:`mopidy.core.PlaylistsController.save`.

- :meth:`mopidy.core.PlaylistsController.rename` has been removed, since
  renaming can be done with :meth:`mopidy.core.PlaylistsController.save`.

- :meth:`mopidy.core.PlaylistsController.get` has been replaced by
  :meth:`mopidy.core.PlaylistsController.filter`.

- The event :meth:`mopidy.core.CoreListener.playlist_changed` has been changed
  to include the playlist that was changed.

*Tracklist:*

- Renamed "current playlist" to "tracklist" everywhere, including the core API
  used by frontends.

- Removed :meth:`mopidy.core.TracklistController.append`. Use
  :meth:`mopidy.core.TracklistController.add` instead, which is now capable of
  adding multiple tracks.

- :meth:`mopidy.core.TracklistController.get` has been replaced by
  :meth:`mopidy.core.TracklistController.filter`.

- :meth:`mopidy.core.TracklistController.remove` can now remove multiple
  tracks, and returns the tracks it removed.

- When the tracklist is changed, we now trigger the new
  :meth:`mopidy.core.CoreListener.tracklist_changed` event. Previously we
  triggered :meth:`mopidy.core.CoreListener.playlist_changed`, which is
  intended for stored playlists, not the tracklist.

*Towards Python 3 support:*

- Make the entire code base use unicode strings by default, and only fall back
  to bytestrings where it is required. Another step closer to Python 3.


v0.8.1 (2012-10-30)
===================

A small maintenance release to fix a bug introduced in 0.8.0 and update Mopidy
to work with Pykka 1.0.

**Dependencies**

- Pykka >= 1.0 is now required.

**Bug fixes**

- :issue:`213`: Fix "streaming task paused, reason not-negotiated" errors
  observed by some users on some Spotify tracks due to a change introduced in
  0.8.0. See the issue for a patch that applies to 0.8.0.

- :issue:`216`: Volume returned by the MPD command `status` contained a
  floating point ``.0`` suffix. This bug was introduced with the large audio
  output and mixer changes in v0.8.0 and broke the MPDroid Android client. It
  now returns an integer again.


v0.8.0 (2012-09-20)
===================

This release does not include any major new features. We've done a major
cleanup of how audio outputs and audio mixers work, and on the way we've
resolved a bunch of related issues.

**Audio output and mixer changes**

- Removed multiple outputs support. Having this feature currently seems to be
  more trouble than what it is worth. The :attr:`mopidy.settings.OUTPUTS`
  setting is no longer supported, and has been replaced with
  :attr:`mopidy.settings.OUTPUT` which is a GStreamer bin description string in
  the same format as ``gst-launch`` expects. Default value is
  ``autoaudiosink``. (Fixes: :issue:`81`, :issue:`115`, :issue:`121`,
  :issue:`159`)

- Switch to pure GStreamer based mixing. This implies that users setup a
  GStreamer bin with a mixer in it in :attr:`mopidy.settings.MIXER`. The
  default value is ``autoaudiomixer``, a custom mixer that attempts to find a
  mixer that will work on your system. If this picks the wrong mixer you can of
  course override it. Setting the mixer to :class:`None` is also supported. MPD
  protocol support for volume has also been updated to return -1 when we have
  no mixer set. ``software`` can be used to force software mixing.

- Removed the Denon hardware mixer, as it is not maintained.

- Updated the NAD hardware mixer to work in the new GStreamer based mixing
  regime. Settings are now passed as GStreamer element properties. In practice
  that means that the following old-style config::

      MIXER = u'mopidy.mixers.nad.NadMixer'
      MIXER_EXT_PORT = u'/dev/ttyUSB0'
      MIXER_EXT_SOURCE = u'Aux'
      MIXER_EXT_SPEAKERS_A = u'On'
      MIXER_EXT_SPEAKERS_B = u'Off'

  Now is reduced to simply::

      MIXER = u'nadmixer port=/dev/ttyUSB0 source=aux speakers-a=on speakers-b=off'

  The ``port`` property defaults to ``/dev/ttyUSB0``, and the rest of the
  properties may be left out if you don't want the mixer to adjust the settings
  on your NAD amplifier when Mopidy is started.

**Changes**

- When unknown settings are encountered, we now check if it's similar to a
  known setting, and suggests to the user what we think the setting should have
  been.

- Added ``mopidy --list-deps`` option that lists required and optional
  dependencies, their current versions, and some other information useful for
  debugging. (Fixes: :issue:`74`)

- Added ``tools/debug-proxy.py`` to tee client requests to two backends and
  diff responses. Intended as a developer tool for checking for MPD protocol
  changes and various client support. Requires gevent, which currently is not a
  dependency of Mopidy.

- Support tracks with only release year, and not a full release date, like e.g.
  Spotify tracks.

- Default value of ``LOCAL_MUSIC_PATH`` has been updated to be
  ``$XDG_MUSIC_DIR``, which on most systems this is set to ``$HOME``. Users of
  local backend that relied on the old default ``~/music`` need to update their
  settings. Note that the code responsible for finding this music now also
  ignores UNIX hidden files and folders.

- File and path settings now support ``$XDG_CACHE_DIR``, ``$XDG_DATA_DIR`` and
  ``$XDG_MUSIC_DIR`` substitution. Defaults for such settings have been updated
  to use this instead of hidden away defaults.

- Playback is now done using ``playbin2`` from GStreamer instead of rolling our
  own. This is the first step towards resolving :issue:`171`.

**Bug fixes**

- :issue:`72`: Created a Spotify track proxy that will switch to using loaded
  data as soon as it becomes available.

- :issue:`150`: Fix bug which caused some clients to block Mopidy completely.
  The bug was caused by some clients sending ``close`` and then shutting down
  the connection right away. This trigged a situation in which the connection
  cleanup code would wait for an response that would never come inside the
  event loop, blocking everything else.

- :issue:`162`: Fixed bug when the MPD command ``playlistinfo`` is used with a
  track position. Track position and CPID was intermixed, so it would cause a
  crash if a CPID matching the track position didn't exist.

- Fixed crash on lookup of unknown path when using local backend.

- :issue:`189`: ``LOCAL_MUSIC_PATH`` and path handling in rest of settings  has
  been updated so all of the code now uses the correct value.

- Fixed incorrect track URIs generated by M3U playlist parsing code. Generated
  tracks are now relative to ``LOCAL_MUSIC_PATH``.

- :issue:`203`: Re-add support for software mixing.


v0.7.3 (2012-08-11)
===================

A small maintenance release to fix a crash affecting a few users, and a couple
of small adjustments to the Spotify backend.

**Changes**

- Fixed crash when logging :exc:`IOError` exceptions on systems using languages
  with non-ASCII characters, like French.

- Move the default location of the Spotify cache from `~/.cache/mopidy` to
  `~/.cache/mopidy/spotify`. You can change this by setting
  :attr:`mopidy.settings.SPOTIFY_CACHE_PATH`.

- Reduce time required to update the Spotify cache on startup. One one
  system/Spotify account, the time from clean cache to ready for use was
  reduced from 35s to 12s.


v0.7.2 (2012-05-07)
===================

This is a maintenance release to make Mopidy 0.7 build on systems without all
of Mopidy's runtime dependencies, like Launchpad PPAs.

**Changes**

- Change from version tuple at :attr:`mopidy.VERSION` to :pep:`386` compliant
  version string at :attr:`mopidy.__version__` to conform to :pep:`396`.


v0.7.1 (2012-04-22)
===================

This is a maintenance release to make Mopidy 0.7 work with pyspotify >= 1.7.

**Changes**

- Don't override pyspotify's ``notify_main_thread`` callback. The default
  implementation is sensible, while our override did nothing.


v0.7.0 (2012-02-25)
===================

Not a big release with regard to features, but this release got some
performance improvements over v0.6, especially for slower Atom systems. It also
fixes a couple of other bugs, including one which made Mopidy crash when using
GStreamer from the prereleases of Ubuntu 12.04.

**Changes**

- The MPD command ``playlistinfo`` is now faster, thanks to John Bäckstrand.

- Added the method
  :meth:`mopidy.backends.base.CurrentPlaylistController.length()`,
  :meth:`mopidy.backends.base.CurrentPlaylistController.index()`, and
  :meth:`mopidy.backends.base.CurrentPlaylistController.slice()` to reduce the
  need for copying the entire current playlist from one thread to another.
  Thanks to John Bäckstrand for pinpointing the issue.

- Fix crash on creation of config and cache directories if intermediate
  directories does not exist. This was especially the case on OS X, where
  ``~/.config`` doesn't exist for most users.

- Fix ``gst.LinkError`` which appeared when using newer versions of GStreamer,
  e.g. on Ubuntu 12.04 Alpha. (Fixes: :issue:`144`)

- Fix crash on mismatching quotation in ``list`` MPD queries. (Fixes:
  :issue:`137`)

- Volume is now reported to be the same as the volume was set to, also when
  internal rounding have been done due to
  :attr:`mopidy.settings.MIXER_MAX_VOLUME` has been set to cap the volume. This
  should make it possible to manage capped volume from clients that only
  increase volume with one step at a time, like ncmpcpp does.


v0.6.1 (2011-12-28)
===================

This is a maintenance release to make Mopidy 0.6 work with pyspotify >= 1.5,
which Mopidy's develop branch have supported for a long time. This should also
make the Debian packages work out of the box again.

**Important changes**

- pyspotify 1.5 or greater is required.

**Changes**

- Spotify playlist folder boundaries are now properly detected. In other words,
  if you use playlist folders, you will no longer get lots of log messages
  about bad playlists.



v0.6.0 (2011-10-09)
===================

The development of Mopidy have been quite slow for the last couple of months,
but we do have some goodies to release which have been idling in the
develop branch since the warmer days of the summer. This release brings support
for the MPD ``idle`` command, which makes it possible for a client wait for
updates from the server instead of polling every second. Also, we've added
support for the MPRIS standard, so that Mopidy can be controlled over D-Bus
from e.g. the Ubuntu Sound Menu.

Please note that 0.6.0 requires some updated dependencies, as listed under
*Important changes* below.

**Important changes**

- Pykka 0.12.3 or greater is required.

- pyspotify 1.4 or greater is required.

- All config, data, and cache locations are now based on the XDG spec.

  - This means that your settings file will need to be moved from
    ``~/.mopidy/settings.py`` to ``~/.config/mopidy/settings.py``.
  - Your Spotify cache will now be stored in ``~/.cache/mopidy`` instead of
    ``~/.mopidy/spotify_cache``.
  - The local backend's ``tag_cache`` should now be in
    ``~/.local/share/mopidy/tag_cache``, likewise your playlists will be in
    ``~/.local/share/mopidy/playlists``.
  - The local client now tries to lookup where your music is via XDG, it will
    fall-back to ``~/music`` or use whatever setting you set manually.

- The MPD command ``idle`` is now supported by Mopidy for the following
  subsystems: player, playlist, options, and mixer. (Fixes: :issue:`32`)

- A new frontend :mod:`mopidy.frontends.mpris` have been added. It exposes
  Mopidy through the `MPRIS interface <http://specifications.freedesktop.org/mpris-spec/latest/>`_ over D-Bus. In
  practice, this makes it possible to control Mopidy through the `Ubuntu Sound
  Menu <https://wiki.ubuntu.com/Sound#menu>`_.

**Changes**

- Replace :attr:`mopidy.backends.base.Backend.uri_handlers` with
  :attr:`mopidy.backends.base.Backend.uri_schemes`, which just takes the part
  up to the colon of an URI, and not any prefix.

- Add Listener API, :mod:`mopidy.listeners`, to be implemented by actors
  wanting to receive events from the backend. This is a formalization of the
  ad hoc events the Last.fm scrobbler has already been using for some time.

- Replaced all of the MPD network code that was provided by asyncore with
  custom stack. This change was made to facilitate support for the ``idle``
  command, and to reduce the number of event loops being used.

- Fix metadata update in Shoutcast streaming. (Fixes: :issue:`122`)

- Unescape all incoming MPD requests. (Fixes: :issue:`113`)

- Increase the maximum number of results returned by Spotify searches from 32
  to 100.

- Send Spotify search queries to pyspotify as unicode objects, as required by
  pyspotify 1.4. (Fixes: :issue:`129`)

- Add setting :attr:`mopidy.settings.MPD_SERVER_MAX_CONNECTIONS`. (Fixes:
  :issue:`134`)

- Remove `destroy()` methods from backend controller and provider APIs, as it
  was not in use and actually not called by any code. Will reintroduce when
  needed.


v0.5.0 (2011-06-15)
===================

Since last time we've added support for audio streaming to SHOUTcast servers
and fixed the longstanding playlist loading issue in the Spotify backend. As
always the release has a bunch of bug fixes and minor improvements.

Please note that 0.5.0 requires some updated dependencies, as listed under
*Important changes* below.

**Important changes**

- If you use the Spotify backend, you *must* upgrade to libspotify 0.0.8 and
  pyspotify 1.3. If you install from APT, libspotify and pyspotify will
  automatically be upgraded. If you are not installing from APT, follow the
  instructions at :ref:`installation`.

- If you have explicitly set the :attr:`mopidy.settings.SPOTIFY_HIGH_BITRATE`
  setting, you must update your settings file. The new setting is named
  :attr:`mopidy.settings.SPOTIFY_BITRATE` and accepts the integer values 96,
  160, and 320.

- Mopidy now supports running with 1 to N outputs at the same time. This
  feature was mainly added to facilitate SHOUTcast support, which Mopidy has
  also gained. In its current state outputs can not be toggled during runtime.

**Changes**

- Local backend:

  - Fix local backend time query errors that where coming from stopped
    pipeline. (Fixes: :issue:`87`)

- Spotify backend:

  - Thanks to Antoine Pierlot-Garcin's recent work on updating and improving
    pyspotify, stored playlists will again load when Mopidy starts. The
    workaround of searching and reconnecting to make the playlists appear are
    no longer necessary. (Fixes: :issue:`59`)

  - Track's that are no longer available in Spotify's archives are now
    "autolinked" to corresponding tracks in other albums, just like the
    official Spotify clients do. (Fixes: :issue:`34`)

- MPD frontend:

  - Refactoring and cleanup. Most notably, all request handlers now get an
    instance of :class:`mopidy.frontends.mpd.dispatcher.MpdContext` as the
    first argument. The new class contains reference to any object in Mopidy
    the MPD protocol implementation should need access to.

  - Close the client connection when the command ``close`` is received.

  - Do not allow access to the command ``kill``.

  - ``commands`` and ``notcommands`` now have correct output if password
    authentication is turned on, but the connected user has not been
    authenticated yet.

- Command line usage:

  - Support passing options to GStreamer. See ``mopidy --help-gst`` for a list
    of available options. (Fixes: :issue:`95`)

  - Improve ``mopidy --list-settings`` output. (Fixes: :issue:`91`)

  - Added ``mopidy --interactive`` for reading missing local settings from
    ``stdin``. (Fixes: :issue:`96`)

  - Improve shutdown procedure at CTRL+C. Add signal handler for ``SIGTERM``,
    which initiates the same shutdown procedure as CTRL+C does.

- Tag cache generator:

  - Made it possible to abort :command:`mopidy-scan` with CTRL+C.

  - Fixed bug regarding handling of bad dates.

  - Use :mod:`logging` instead of ``print`` statements.

  - Found and worked around strange WMA metadata behaviour.

- Backend API:

  - Calling on :meth:`mopidy.backends.base.playback.PlaybackController.next`
    and :meth:`mopidy.backends.base.playback.PlaybackController.previous` no
    longer implies that playback should be started. The playback state--whether
    playing, paused or stopped--will now be kept.

  - The method
    :meth:`mopidy.backends.base.playback.PlaybackController.change_track`
    has been added. Like ``next()``, and ``prev()``, it changes the current
    track without changing the playback state.


v0.4.1 (2011-05-06)
===================

This is a bug fix release fixing audio problems on older GStreamer and some
minor bugs.


**Bug fixes**

- Fix broken audio on at least GStreamer 0.10.30, which affects Ubuntu 10.10.
  The GStreamer `appsrc` bin wasn't being linked due to lack of default caps.
  (Fixes: :issue:`85`)

- Fix crash in :mod:`mopidy.mixers.nad` that occures at startup when the
  :mod:`io` module is available. We used an `eol` keyword argument which is
  supported by :meth:`serial.FileLike.readline`, but not by
  :meth:`io.RawBaseIO.readline`.  When the :mod:`io` module is available, it is
  used by PySerial instead of the `FileLike` implementation.

- Fix UnicodeDecodeError in MPD frontend on non-english locale. Thanks to
  Antoine Pierlot-Garcin for the patch. (Fixes: :issue:`88`)

- Do not create Pykka proxies that are not going to be used in
  :mod:`mopidy.core`. The underlying actor may already intentionally be dead,
  and thus the program may crash on creating a proxy it doesn't need. Combined
  with the Pykka 0.12.2 release this fixes a crash in the Last.fm frontend
  which may occur when all dependencies are installed, but the frontend isn't
  configured. (Fixes: :issue:`84`)


v0.4.0 (2011-04-27)
===================

Mopidy 0.4.0 is another release without major feature additions. In 0.4.0 we've
fixed a bunch of issues and bugs, with the help of several new contributors
who are credited in the changelog below. The major change of 0.4.0 is an
internal refactoring which clears way for future features, and which also make
Mopidy work on Python 2.7. In other words, Mopidy 0.4.0 works on Ubuntu 11.04
and Arch Linux.

Please note that 0.4.0 requires some updated dependencies, as listed under
*Important changes* below. Also, the known bug in the Spotify playlist
loading from Mopidy 0.3.0 is still present.

.. warning:: Known bug in Spotify playlist loading

    There is a known bug in the loading of Spotify playlists. To avoid the bug,
    follow the simple workaround described at :issue:`59`.


**Important changes**

- Mopidy now depends on `Pykka <http://pykka.readthedocs.org/>`_ >=0.12. If you
  install from APT, Pykka will automatically be installed. If you are not
  installing from APT, you may install Pykka from PyPI::

      sudo pip install -U Pykka

- If you use the Spotify backend, you *should* upgrade to libspotify 0.0.7 and
  the latest pyspotify from the Mopidy developers. If you install from APT,
  libspotify and pyspotify will automatically be upgraded. If you are not
  installing from APT, follow the instructions at :ref:`installation`.


**Changes**

- Mopidy now use Pykka actors for thread management and inter-thread
  communication. The immediate advantage of this is that Mopidy now works on
  Python 2.7, which is the default on e.g. Ubuntu 11.04. (Fixes: :issue:`66`)

- Spotify backend:

  - Fixed multiple segmentation faults due to bugs in Pyspotify. Thanks to
    Antoine Pierlot-Garcin and Jamie Kirkpatrick for patches to Pyspotify.

  - Better error messages on wrong login or network problems. Thanks to Antoine
    Pierlot-Garcin for patches to Mopidy and Pyspotify. (Fixes: :issue:`77`)

  - Reduce log level for trivial log messages from warning to info. (Fixes:
    :issue:`71`)

  - Pause playback on network connection errors. (Fixes: :issue:`65`)

- Local backend:

  - Fix crash in :command:`mopidy-scan` if a track has no artist name. Thanks
    to Martins Grunskis for test and patch and "octe" for patch.

  - Fix crash in `tag_cache` parsing if a track has no total number of tracks
    in the album. Thanks to Martins Grunskis for the patch.

- MPD frontend:

  - Add support for "date" queries to both the ``find`` and ``search``
    commands. This makes media library browsing in ncmpcpp work, though very
    slow due to all the meta data requests to Spotify.

  - Add support for ``play "-1"`` when in playing or paused state, which fixes
    resume and addition of tracks to the current playlist while playing for the
    MPoD client.

  - Fix bug where ``status`` returned ``song: None``, which caused MPDroid to
    crash. (Fixes: :issue:`69`)

  - Gracefully fallback to IPv4 sockets on systems that supports IPv6, but has
    turned it off. (Fixes: :issue:`75`)

- GStreamer output:

  - Use ``uridecodebin`` for playing audio from both Spotify and the local
    backend. This contributes to support for multiple backends simultaneously.

- Settings:

  - Fix crash on ``mopidy --list-settings`` on clean installation. Thanks to
    Martins Grunskis for the bug report and patch. (Fixes: :issue:`63`)

- Packaging:

  - Replace test data symlinks with real files to avoid symlink issues when
    installing with pip. (Fixes: :issue:`68`)

- Debugging:

  - Include platform, architecture, Linux distribution, and Python version in
    the debug log, to ease debugging of issues with attached debug logs.


v0.3.1 (2011-01-22)
===================

A couple of fixes to the 0.3.0 release is needed to get a smooth installation.

**Bug fixes**

- The Spotify application key was missing from the Python package.

- Installation of the Python package as a normal user failed because it did not
  have permissions to install ``mopidy.desktop``. The file is now only
  installed if the installation is executed as the root user.


v0.3.0 (2011-01-22)
===================

Mopidy 0.3.0 brings a bunch of small changes all over the place, but no large
changes. The main features are support for high bitrate audio from Spotify, and
MPD password authentication.

Regarding the docs, we've improved the :ref:`installation instructions
<installation>` and done a bit of testing of the available :ref:`Android
<android_mpd_clients>` and :ref:`iOS clients <ios_mpd_clients>` for MPD.

Please note that 0.3.0 requires some updated dependencies, as listed under
*Important changes* below. Also, there is a known bug in the Spotify playlist
loading, as described below. As the bug will take some time to fix and has a
known workaround, we did not want to delay the release while waiting for a fix
to this problem.


.. warning:: Known bug in Spotify playlist loading

    There is a known bug in the loading of Spotify playlists. This bug affects
    both Mopidy 0.2.1 and 0.3.0, given that you use libspotify 0.0.6. To avoid
    the bug, either use Mopidy 0.2.1 with libspotify 0.0.4, or use either
    Mopidy version with libspotify 0.0.6 and follow the simple workaround
    described at :issue:`59`.


**Important changes**

- If you use the Spotify backend, you need to upgrade to libspotify 0.0.6 and
  the latest pyspotify from the Mopidy developers. Follow the instructions at
  :ref:`installation`.

- If you use the Last.fm frontend, you need to upgrade to pylast 0.5.7. Run
  ``sudo pip install --upgrade pylast`` or install Mopidy from APT.


**Changes**

- Spotify backend:

  - Support high bitrate (320k) audio. Set the new setting
    :attr:`mopidy.settings.SPOTIFY_HIGH_BITRATE` to :class:`True` to switch to
    high bitrate audio.

  - Rename :mod:`mopidy.backends.libspotify` to :mod:`mopidy.backends.spotify`.
    If you have set :attr:`mopidy.settings.BACKENDS` explicitly, you may need
    to update the setting's value.

  - Catch and log error caused by playlist folder boundaries being threated as
    normal playlists. More permanent fix requires support for checking playlist
    types in pyspotify (see :issue:`62`).

  - Fix crash on failed lookup of track by URI. (Fixes: :issue:`60`)

- Local backend:

  - Add :command:`mopidy-scan` command to generate ``tag_cache`` files without
    any help from the original MPD server. See
    "Generating a local library" for instructions on how to use it.

  - Fix support for UTF-8 encoding in tag caches.

- MPD frontend:

  - Add support for password authentication. See
    :attr:`mopidy.settings.MPD_SERVER_PASSWORD` for details on how to use it.
    (Fixes: :issue:`41`)

  - Support ``setvol 50`` without quotes around the argument. Fixes volume
    control in Droid MPD.

  - Support ``seek 1 120`` without quotes around the arguments. Fixes seek in
    Droid MPD.

- Last.fm frontend:

  - Update to use Last.fm's new Scrobbling 2.0 API, as the old Submissions
    Protocol 1.2.1 is deprecated. (Fixes: :issue:`33`)

  - Fix crash when track object does not contain all the expected meta data.

  - Fix crash when response from Last.fm cannot be decoded as UTF-8. (Fixes:
    :issue:`37`)

  - Fix crash when response from Last.fm contains invalid XML.

  - Fix crash when response from Last.fm has an invalid HTTP status line.

- Mixers:

  - Support use of unicode strings for settings specific to
    :mod:`mopidy.mixers.nad`.

- Settings:

  - Automatically expand the "~" characted to the user's home directory and
    make the path absolute for settings with names ending in ``_PATH`` or
    ``_FILE``.

  - Rename the following settings. The settings validator will warn you if you
    need to change your local settings.

    - ``LOCAL_MUSIC_FOLDER`` to :attr:`mopidy.settings.LOCAL_MUSIC_PATH`
    - ``LOCAL_PLAYLIST_FOLDER`` to
      :attr:`mopidy.settings.LOCAL_PLAYLIST_PATH`
    - ``LOCAL_TAG_CACHE`` to :attr:`mopidy.settings.LOCAL_TAG_CACHE_FILE`
    - ``SPOTIFY_LIB_CACHE`` to :attr:`mopidy.settings.SPOTIFY_CACHE_PATH`

  - Fix bug which made settings set to :class:`None` or 0 cause a
    :exc:`mopidy.SettingsError` to be raised.

- Packaging and distribution:

  - Setup APT repository and create Debian packages of Mopidy. See
    :ref:`installation` for instructions for how to install Mopidy, including
    all dependencies, from APT.

  - Install ``mopidy.desktop`` file that makes Mopidy available from e.g. Gnome
    application menus.

- API:

  - Rename and generalize ``Playlist._with(**kwargs)`` to
    :meth:`mopidy.models.ImmutableObject.copy`.

  - Add ``musicbrainz_id`` field to :class:`mopidy.models.Artist`,
    :class:`mopidy.models.Album`, and :class:`mopidy.models.Track`.

  - Prepare for multi-backend support (see :issue:`40`) by introducing the
    :ref:`provider concept <concepts>`. Split the backend API into a
    :ref:`backend controller API <core-api>` (for frontend use)
    and a :ref:`backend provider API <backend-api>` (for backend
    implementation use), which includes the following changes:

    - Rename ``BaseBackend`` to :class:`mopidy.backends.base.Backend`.
    - Rename ``BaseCurrentPlaylistController`` to
      :class:`mopidy.backends.base.CurrentPlaylistController`.
    - Split ``BaseLibraryController`` to
      :class:`mopidy.backends.base.LibraryController` and
      :class:`mopidy.backends.base.BaseLibraryProvider`.
    - Split ``BasePlaybackController`` to
      :class:`mopidy.backends.base.PlaybackController` and
      :class:`mopidy.backends.base.BasePlaybackProvider`.
    - Split ``BaseStoredPlaylistsController`` to
      :class:`mopidy.backends.base.StoredPlaylistsController` and
      :class:`mopidy.backends.base.BaseStoredPlaylistsProvider`.

  - Move ``BaseMixer`` to :class:`mopidy.mixers.base.BaseMixer`.

  - Add docs for the current non-stable output API,
    :class:`mopidy.outputs.base.BaseOutput`.


v0.2.1 (2011-01-07)
===================

This is a maintenance release without any new features.

**Bug fixes**

- Fix crash in :mod:`mopidy.frontends.lastfm` which occurred at playback if
  either :mod:`pylast` was not installed or the Last.fm scrobbling was not
  correctly configured. The scrobbling thread now shuts properly down at
  failure.


v0.2.0 (2010-10-24)
===================

In Mopidy 0.2.0 we've added a `Last.fm <http://www.last.fm/>`_ scrobbling
support, which means that Mopidy now can submit meta data about the tracks you
play to your Last.fm profile. See :mod:`mopidy.frontends.lastfm` for
details on new dependencies and settings. If you use Mopidy's Last.fm support,
please join the `Mopidy group at Last.fm <http://www.last.fm/group/Mopidy>`_.

With the exception of the work on the Last.fm scrobbler, there has been a
couple of quiet months in the Mopidy camp. About the only thing going on, has
been stabilization work and bug fixing. All bugs reported on GitHub, plus some,
have been fixed in 0.2.0. Thus, we hope this will be a great release!

We've worked a bit on OS X support, but not all issues are completely solved
yet. :issue:`25`  is the one that is currently blocking OS X support. Any help
solving it will be greatly appreciated!

Finally, please :ref:`update your pyspotify installation <installation>` when
upgrading to Mopidy 0.2.0. The latest pyspotify got a fix for the segmentation
fault that occurred when playing music and searching at the same time, thanks
to Valentin David.

**Important changes**

- Added a Last.fm scrobbler. See :mod:`mopidy.frontends.lastfm` for details.

**Changes**

- Logging and command line options:

  - Simplify the default log format,
    :attr:`mopidy.settings.CONSOLE_LOG_FORMAT`. From a user's point of view:
    Less noise, more information.
  - Rename the ``mopidy --dump`` command line option to
    :option:`mopidy --save-debug-log`.
  - Rename setting :attr:`mopidy.settings.DUMP_LOG_FORMAT` to
    :attr:`mopidy.settings.DEBUG_LOG_FORMAT` and use it for
    :option:`mopidy --verbose` too.
  - Rename setting :attr:`mopidy.settings.DUMP_LOG_FILENAME` to
    :attr:`mopidy.settings.DEBUG_LOG_FILENAME`.

- MPD frontend:

  - MPD command ``list`` now supports queries by artist, album name, and date,
    as used by e.g. the Ario client. (Fixes: :issue:`20`)
  - MPD command ``add ""`` and ``addid ""`` now behaves as expected. (Fixes
    :issue:`16`)
  - MPD command ``playid "-1"`` now correctly resumes playback if paused.

- Random mode:

  - Fix wrong behavior on end of track and next after random mode has been
    used. (Fixes: :issue:`18`)
  - Fix infinite recursion loop crash on playback of non-playable tracks when
    in random mode. (Fixes :issue:`17`)
  - Fix assertion error that happened if one removed tracks from the current
    playlist, while in random mode. (Fixes :issue:`22`)

- Switched from using subprocesses to threads. (Fixes: :issue:`14`)
- :mod:`mopidy.outputs.gstreamer`: Set ``caps`` on the ``appsrc`` bin before
  use. This makes sound output work with GStreamer >= 0.10.29, which includes
  the versions used in Ubuntu 10.10 and on OS X if using Homebrew. (Fixes:
  :issue:`21`, :issue:`24`, contributes to :issue:`14`)
- Improved handling of uncaught exceptions in threads. The entire process
  should now exit immediately.


v0.1.0 (2010-08-23)
===================

After three weeks of long nights and sprints we're finally pleased enough with
the state of Mopidy to remove the alpha label, and do a regular release.

Mopidy 0.1.0 got important improvements in search functionality, working track
position seeking, no known stability issues, and greatly improved MPD client
support. There are lots of changes since 0.1.0a3, and we urge you to at least
read the *important changes* below.

This release does not support OS X. We're sorry about that, and are working on
fixing the OS X issues for a future release. You can track the progress at
:issue:`14`.

**Important changes**

- License changed from GPLv2 to Apache License, version 2.0.
- GStreamer is now a required dependency. See our :ref:`GStreamer installation
  docs <installation>`.
- :mod:`mopidy.backends.libspotify` is now the default backend.
  :mod:`mopidy.backends.despotify` is no longer available. This means that you
  need to install the :ref:`dependencies for libspotify <installation>`.
- If you used :mod:`mopidy.backends.libspotify` previously, pyspotify must be
  updated when updating to this release, to get working seek functionality.
- :attr:`mopidy.settings.SERVER_HOSTNAME` and
  :attr:`mopidy.settings.SERVER_PORT` has been renamed to
  :attr:`mopidy.settings.MPD_SERVER_HOSTNAME` and
  :attr:`mopidy.settings.MPD_SERVER_PORT` to allow for multiple frontends in
  the future.

**Changes**

- Exit early if not Python >= 2.6, < 3.
- Validate settings at startup and print useful error messages if the settings
  has not been updated or anything is misspelled.
- Add command line option ``mopidy --list-settings`` to print the currently
  active settings.
- Include Sphinx scripts for building docs, pylintrc, tests and test data in
  the packages created by ``setup.py`` for i.e. PyPI.
- MPD frontend:

  - Search improvements, including support for multi-word search.
  - Fixed ``play "-1"`` and ``playid "-1"`` behaviour when playlist is empty
    or when a current track is set.
  - Support ``plchanges "-1"`` to work better with MPDroid.
  - Support ``pause`` without arguments to work better with MPDroid.
  - Support ``plchanges``, ``play``, ``consume``, ``random``, ``repeat``, and
    ``single`` without quotes to work better with BitMPC.
  - Fixed deletion of the currently playing track from the current playlist,
    which crashed several clients.
  - Implement ``seek`` and ``seekid``.
  - Fix ``playlistfind`` output so the correct song is played when playing
    songs directly from search results in GMPC.
  - Fix ``load`` so that one can append a playlist to the current playlist, and
    make it return the correct error message if the playlist is not found.
  - Support for single track repeat added. (Fixes: :issue:`4`)
  - Relocate from :mod:`mopidy.mpd` to :mod:`mopidy.frontends.mpd`.
  - Split gigantic protocol implementation into eleven modules.
  - Rename ``mopidy.frontends.mpd.{serializer => translator}`` to match naming
    in backends.
  - Remove setting :attr:`mopidy.settings.SERVER` and
    :attr:`mopidy.settings.FRONTEND` in favour of the new
    :attr:`mopidy.settings.FRONTENDS`.
  - Run MPD server in its own process.

- Backends:

  - Rename :mod:`mopidy.backends.gstreamer` to :mod:`mopidy.backends.local`.
  - Remove :mod:`mopidy.backends.despotify`, as Despotify is little maintained
    and the Libspotify backend is working much better. (Fixes: :issue:`9`,
    :issue:`10`, :issue:`13`)
  - A Spotify application key is now bundled with the source.
    :attr:`mopidy.settings.SPOTIFY_LIB_APPKEY` is thus removed.
  - If failing to play a track, playback will skip to the next track.
  - Both :mod:`mopidy.backends.libspotify` and :mod:`mopidy.backends.local`
    have been rewritten to use the new common GStreamer audio output module,
    :mod:`mopidy.outputs.gstreamer`.

- Mixers:

  - Added new :mod:`mopidy.mixers.gstreamer_software.GStreamerSoftwareMixer`
    which now is the default mixer on all platforms.
  - New setting :attr:`mopidy.settings.MIXER_MAX_VOLUME` for capping the
    maximum output volume.

- Backend API:

  - Relocate from :mod:`mopidy.backends` to :mod:`mopidy.backends.base`.
  - The ``id`` field of :class:`mopidy.models.Track` has been removed, as it is
    no longer needed after the CPID refactoring.
  - :meth:`mopidy.backends.base.BaseBackend()` now accepts an
    ``output_queue`` which it can use to send messages (i.e. audio data)
    to the output process.
  - :meth:`mopidy.backends.base.BaseLibraryController.find_exact()` now accepts
    keyword arguments of the form ``find_exact(artist=['foo'],
    album=['bar'])``.
  - :meth:`mopidy.backends.base.BaseLibraryController.search()` now accepts
    keyword arguments of the form ``search(artist=['foo', 'fighters'],
    album=['bar', 'grooves'])``.
  - :meth:`mopidy.backends.base.BaseCurrentPlaylistController.append()`
    replaces
    :meth:`mopidy.backends.base.BaseCurrentPlaylistController.load()`. Use
    :meth:`mopidy.backends.base.BaseCurrentPlaylistController.clear()` if you
    want to clear the current playlist.
  - The following fields in
    :class:`mopidy.backends.base.BasePlaybackController` has been renamed to
    reflect their relation to methods called on the controller:

    - ``next_track`` to ``track_at_next``
    - ``next_cp_track`` to ``cp_track_at_next``
    - ``previous_track`` to ``track_at_previous``
    - ``previous_cp_track`` to ``cp_track_at_previous``

  - :attr:`mopidy.backends.base.BasePlaybackController.track_at_eot` and
    :attr:`mopidy.backends.base.BasePlaybackController.cp_track_at_eot` has
    been added to better handle the difference between the user pressing next
    and the current track ending.
  - Rename
    :meth:`mopidy.backends.base.BasePlaybackController.new_playlist_loaded_callback()`
    to
    :meth:`mopidy.backends.base.BasePlaybackController.on_current_playlist_change()`.
  - Rename
    :meth:`mopidy.backends.base.BasePlaybackController.end_of_track_callback()`
    to :meth:`mopidy.backends.base.BasePlaybackController.on_end_of_track()`.
  - Remove :meth:`mopidy.backends.base.BaseStoredPlaylistsController.search()`
    since it was barely used, untested, and we got no use case for non-exact
    search in stored playlists yet. Use
    :meth:`mopidy.backends.base.BaseStoredPlaylistsController.get()` instead.


v0.1.0a3 (2010-08-03)
=====================

In the last two months, Mopidy's MPD frontend has gotten lots of stability
fixes and error handling improvements, proper support for having the same track
multiple times in a playlist, and support for IPv6. We have also fixed the
choppy playback on the libspotify backend. For the road ahead of us, we got an
updated release roadmap with our goals for the 0.1 to 0.3 releases.

Enjoy the best alpha relase of Mopidy ever :-)

**Changes**

- MPD frontend:

  - Support IPv6.
  - ``addid`` responds properly on errors instead of crashing.
  - ``commands`` support, which makes RelaXXPlayer work with Mopidy. (Fixes:
    :issue:`6`)
  - Does no longer crash on invalid data, i.e. non-UTF-8 data.
  - ``ACK`` error messages are now MPD-compliant, which should make clients
    handle errors from Mopidy better.
  - Requests to existing commands with wrong arguments are no longer reported
    as unknown commands.
  - ``command_list_end`` before ``command_list_start`` now returns unknown
    command error instead of crashing.
  - ``list`` accepts field argument without quotes and capitalized, to work
    with GMPC and ncmpc.
  - ``noidle`` command now returns ``OK`` instead of an error. Should make some
    clients work a bit better.
  - Having multiple identical tracks in a playlist is now working properly.
    (CPID refactoring)

- Despotify backend:

  - Catch and log :exc:`spytify.SpytifyError`. (Fixes: :issue:`11`)

- Libspotify backend:

  - Fix choppy playback using the Libspotify backend by using blocking ALSA
    mode. (Fixes: :issue:`7`)

- Backend API:

  - A new data structure called ``cp_track`` is now used in the current
    playlist controller and the playback controller. A ``cp_track`` is a
    two-tuple of (CPID integer, :class:`mopidy.models.Track`), identifying an
    instance of a track uniquely within the current playlist.
  - :meth:`mopidy.backends.BaseCurrentPlaylistController.load()` now accepts
    lists of :class:`mopidy.models.Track` instead of
    :class:`mopidy.models.Playlist`, as none of the other fields on the
    ``Playlist`` model was in use.
  - :meth:`mopidy.backends.BaseCurrentPlaylistController.add()` now returns the
    ``cp_track`` added to the current playlist.
  - :meth:`mopidy.backends.BaseCurrentPlaylistController.remove()` now takes
    criterias, just like
    :meth:`mopidy.backends.BaseCurrentPlaylistController.get()`.
  - :meth:`mopidy.backends.BaseCurrentPlaylistController.get()` now returns a
    ``cp_track``.
  - :attr:`mopidy.backends.BaseCurrentPlaylistController.tracks` is now
    read-only. Use the methods to change its contents.
  - :attr:`mopidy.backends.BaseCurrentPlaylistController.cp_tracks` is a
    read-only list of ``cp_track``. Use the methods to change its contents.
  - :attr:`mopidy.backends.BasePlaybackController.current_track` is now
    just for convenience and read-only. To set the current track, assign a
    ``cp_track`` to
    :attr:`mopidy.backends.BasePlaybackController.current_cp_track`.
  - :attr:`mopidy.backends.BasePlaybackController.current_cpid` is the
    read-only CPID of the current track.
  - :attr:`mopidy.backends.BasePlaybackController.next_cp_track` is the
    next ``cp_track`` in the playlist.
  - :attr:`mopidy.backends.BasePlaybackController.previous_cp_track` is
    the previous ``cp_track`` in the playlist.
  - :meth:`mopidy.backends.BasePlaybackController.play()` now takes a
    ``cp_track``.


v0.1.0a2 (2010-06-02)
=====================

It has been a rather slow month for Mopidy, but we would like to keep up with
the established pace of at least a release per month.

**Changes**

- Improvements to MPD protocol handling, making Mopidy work much better with a
  group of clients, including ncmpc, MPoD, and Theremin.
- New command line flag ``mopidy --dump`` for dumping debug log to ``dump.log``
  in the current directory.
- New setting :attr:`mopidy.settings.MIXER_ALSA_CONTROL` for forcing what ALSA
  control :class:`mopidy.mixers.alsa.AlsaMixer` should use.


v0.1.0a1 (2010-05-04)
=====================

Since the previous release Mopidy has seen about 300 commits, more than 200 new
tests, a libspotify release, and major feature additions to Spotify. The new
releases from Spotify have lead to updates to our dependencies, and also to new
bugs in Mopidy. Thus, this is primarily a bugfix release, even though the not
yet finished work on a GStreamer backend have been merged.

All users are recommended to upgrade to 0.1.0a1, and should at the same time
ensure that they have the latest versions of our dependencies: Despotify r508
if you are using DespotifyBackend, and pyspotify 1.1 with libspotify 0.0.4 if
you are using LibspotifyBackend.

As always, report problems at our IRC channel or our issue tracker. Thanks!

**Changes**

- Backend API changes:

  - Removed ``backend.playback.volume`` wrapper. Use ``backend.mixer.volume``
    directly.
  - Renamed ``backend.playback.playlist_position`` to
    ``current_playlist_position`` to match naming of ``current_track``.
  - Replaced ``get_by_id()`` with a more flexible ``get(**criteria)``.

- Merged the ``gstreamer`` branch from Thomas Adamcik:

  - More than 200 new tests, and thus several bug fixes to existing code.
  - Several new generic features, like shuffle, consume, and playlist repeat.
    (Fixes: :issue:`3`)
  - **[Work in Progress]** A new backend for playing music from a local music
    archive using the GStreamer library.

- Made :class:`mopidy.mixers.alsa.AlsaMixer` work on machines without a mixer
  named "Master".
- Make :class:`mopidy.backends.DespotifyBackend` ignore local files in
  playlists (feature added in Spotify 0.4.3). Reported by Richard Haugen Olsen.
- And much more.


v0.1.0a0 (2010-03-27)
=====================

"*Release early. Release often. Listen to your customers.*" wrote Eric S.
Raymond in *The Cathedral and the Bazaar*.

Three months of development should be more than enough. We have more to do, but
Mopidy is working and usable. 0.1.0a0 is an alpha release, which basicly means
we will still change APIs, add features, etc. before the final 0.1.0 release.
But the software is usable as is, so we release it. Please give it a try and
give us feedback, either at our IRC channel or through the `issue tracker
<https://github.com/mopidy/mopidy/issues>`_. Thanks!

**Changes**

- Initial version. No changelog available.
