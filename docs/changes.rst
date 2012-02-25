*******
Changes
*******

This change log is used to track all major changes to Mopidy.

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
  Mopidy through the `MPRIS interface <http://www.mpris.org/>`_ over D-Bus. In
  practice, this makes it possible to control Mopidy through the `Ubuntu Sound
  Menu <https://wiki.ubuntu.com/SoundMenu>`_.

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
  instructions at :doc:`/installation/libspotify/`.

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

  - Support passing options to GStreamer. See :option:`--help-gst` for a list
    of available options. (Fixes: :issue:`95`)

  - Improve :option:`--list-settings` output. (Fixes: :issue:`91`)

  - Added :option:`--interactive` for reading missing local settings from
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
  installing from APT, follow the instructions at
  :doc:`/installation/libspotify/`.


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

  - Fix crash on ``--list-settings`` on clean installation. Thanks to Martins
    Grunskis for the bug report and patch. (Fixes: :issue:`63`)

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
  :doc:`/installation/libspotify/`.

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
    any help from the original MPD server. See :ref:`generating_a_tag_cache`
    for instructions on how to use it.

  - Fix support for UTF-8 encoding in tag caches.

- MPD frontend:

  - Add support for password authentication. See
    :attr:`mopidy.settings.MPD_SERVER_PASSWORD` and
    :ref:`use_mpd_on_a_network` for details on how to use it. (Fixes:
    :issue:`41`)

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

  - Setup APT repository and crate Debian packages of Mopidy. See
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
    :ref:`provider concept <backend-concepts>`. Split the backend API into a
    :ref:`backend controller API <backend-controller-api>` (for frontend use)
    and a :ref:`backend provider API <backend-provider-api>` (for backend
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

Finally, please :ref:`update your pyspotify installation
<pyspotify_installation>` when upgrading to Mopidy 0.2.0. The latest pyspotify
got a fix for the segmentation fault that occurred when playing music and
searching at the same time, thanks to Valentin David.

**Important changes**

- Added a Last.fm scrobbler. See :mod:`mopidy.frontends.lastfm` for details.

**Changes**

- Logging and command line options:

  - Simplify the default log format,
    :attr:`mopidy.settings.CONSOLE_LOG_FORMAT`. From a user's point of view:
    Less noise, more information.
  - Rename the :option:`--dump` command line option to
    :option:`--save-debug-log`.
  - Rename setting :attr:`mopidy.settings.DUMP_LOG_FORMAT` to
    :attr:`mopidy.settings.DEBUG_LOG_FORMAT` and use it for :option:`--verbose`
    too.
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
- GStreamer is now a required dependency. See our :doc:`GStreamer installation
  docs <installation/gstreamer>`.
- :mod:`mopidy.backends.libspotify` is now the default backend.
  :mod:`mopidy.backends.despotify` is no longer available. This means that you
  need to install the :doc:`dependencies for libspotify
  <installation/libspotify>`.
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
- Add command line option :option:`--list-settings` to print the currently
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
updated :doc:`release roadmap <development/roadmap>` with our goals for the 0.1
to 0.3 releases.

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
- New command line flag :option:`--dump` for dumping debug log to ``dump.log``
  in the current directory.
- New setting :attr:`mopidy.settings.MIXER_ALSA_CONTROL` for forcing what ALSA
  control :class:`mopidy.mixers.alsa.AlsaMixer` should use.


v0.1.0a1 (2010-05-04)
=====================

Since the previous release Mopidy has seen about 300 commits, more than 200 new
tests, a libspotify release, and major feature additions to Spotify. The new
releases from Spotify have lead to updates to our dependencies, and also to new
bugs in Mopidy. Thus, this is primarily a bugfix release, even though the not
yet finished work on a Gstreamer backend have been merged.

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
    archive using the Gstreamer library.

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
<http://github.com/mopidy/mopidy/issues>`_. Thanks!

**Changes**

- Initial version. No changelog available.
