"""
All available settings and their default values.

.. warning::

    Do *not* change settings directly in :mod:`mopidy.settings`. Instead, add a
    file called ``~/.config/mopidy/settings.py`` and redefine settings there.
"""

#: List of playback backends to use. See :mod:`mopidy.backends` for all
#: available backends.
#:
#: Default::
#:
#:     BACKENDS = (u'mopidy.backends.spotify.SpotifyBackend',)
#:
#: Other typical values::
#:
#:     BACKENDS = (u'mopidy.backends.local.LocalBackend',)
#:
#: .. note::
#:     Currently only the first backend in the list is used.
BACKENDS = (
    u'mopidy.backends.spotify.SpotifyBackend',
)

#: The log format used for informational logging.
#:
#: See http://docs.python.org/library/logging.html#formatter-objects for
#: details on the format.
CONSOLE_LOG_FORMAT = u'%(levelname)-8s %(message)s'

#: The log format used for debug logging.
#:
#: See http://docs.python.org/library/logging.html#formatter-objects for
#: details on the format.
DEBUG_LOG_FORMAT = u'%(levelname)-8s %(asctime)s' + \
    ' [%(process)d:%(threadName)s] %(name)s\n  %(message)s'

#: The file to dump debug log data to when Mopidy is run with the
#: :option:`--save-debug-log` option.
#:
#: Default::
#:
#:     DEBUG_LOG_FILENAME = u'mopidy.log'
DEBUG_LOG_FILENAME = u'mopidy.log'

#: Location of the Mopidy .desktop file.
#:
#: Used by :mod:`mopidy.frontends.mpris`.
#:
#: Default::
#:
#:     DESKTOP_FILE = u'/usr/share/applications/mopidy.desktop'
DESKTOP_FILE = u'/usr/share/applications/mopidy.desktop'

#: List of server frontends to use.
#:
#: Default::
#:
#:     FRONTENDS = (
#:         u'mopidy.frontends.mpd.MpdFrontend',
#:         u'mopidy.frontends.lastfm.LastfmFrontend',
#:         u'mopidy.frontends.mpris.MprisFrontend',
#:     )
FRONTENDS = (
    u'mopidy.frontends.mpd.MpdFrontend',
    u'mopidy.frontends.lastfm.LastfmFrontend',
    u'mopidy.frontends.mpris.MprisFrontend',
)

#: Your `Last.fm <http://www.last.fm/>`_ username.
#:
#: Used by :mod:`mopidy.frontends.lastfm`.
LASTFM_USERNAME = u''

#: Your `Last.fm <http://www.last.fm/>`_ password.
#:
#: Used by :mod:`mopidy.frontends.lastfm`.
LASTFM_PASSWORD = u''

#: Path to folder with local music.
#:
#: Used by :mod:`mopidy.backends.local`.
#:
#: Default::
#:
#:    LOCAL_MUSIC_PATH = u'$XDG_MUSIC_DIR'
LOCAL_MUSIC_PATH = u'$XDG_MUSIC_DIR'

#: Path to playlist folder with m3u files for local music.
#:
#: Used by :mod:`mopidy.backends.local`.
#:
#: Default::
#:
#:    LOCAL_PLAYLIST_PATH = u'$XDG_DATA_DIR/mopidy/playlists'
LOCAL_PLAYLIST_PATH = u'$XDG_DATA_DIR/mopidy/playlists'

#: Path to tag cache for local music.
#:
#: Used by :mod:`mopidy.backends.local`.
#:
#: Default::
#:
#:    LOCAL_TAG_CACHE_FILE = u'$XDG_DATA_DIR/mopidy/tag_cache'
LOCAL_TAG_CACHE_FILE = u'$XDG_DATA_DIR/mopidy/tag_cache'

#: Sound mixer to use.
#:
#: Expects a GStreamer mixer to use, typical values are:
#: ``alsamixer``, ``pulsemixer``, ``ossmixer``, and ``oss4mixer``.
#:
#: Setting this to :class:`None` turns off volume control. ``software``
#: can be used to force software mixing in the application.
#:
#: Default::
#:
#:     MIXER = u'autoaudiomixer'
MIXER = u'autoaudiomixer'

#: Sound mixer track to use.
#:
#: Name of the mixer track to use. If this is not set we will try to find the
#: master output track. As an example, using ``alsamixer`` you would
#: typically set this to ``Master`` or ``PCM``.
#:
#: Default::
#:
#:     MIXER_TRACK = None
MIXER_TRACK = None

#: Which address Mopidy's MPD server should bind to.
#:
#: Used by :mod:`mopidy.frontends.mpd`.
#:
#: Examples:
#:
#: ``127.0.0.1``
#:     Listens only on the IPv4 loopback interface. Default.
#: ``::1``
#:     Listens only on the IPv6 loopback interface.
#: ``0.0.0.0``
#:     Listens on all IPv4 interfaces.
#: ``::``
#:     Listens on all interfaces, both IPv4 and IPv6.
MPD_SERVER_HOSTNAME = u'127.0.0.1'

#: Which TCP port Mopidy's MPD server should listen to.
#:
#: Used by :mod:`mopidy.frontends.mpd`.
#:
#: Default: 6600
MPD_SERVER_PORT = 6600

#: The password required for connecting to the MPD server.
#:
#: Used by :mod:`mopidy.frontends.mpd`.
#:
#: Default: :class:`None`, which means no password required.
MPD_SERVER_PASSWORD = None

#: The maximum number of concurrent connections the MPD server will accept.
#:
#: Used by :mod:`mopidy.frontends.mpd`.
#:
#: Default: 20
MPD_SERVER_MAX_CONNECTIONS = 20

#: Output to use. See :mod:`mopidy.outputs` for all available backends
#:
#: Default::
#:
#:     OUTPUT = u'autoaudiosink'
OUTPUT = u'autoaudiosink'

#: Path to the Spotify cache.
#:
#: Used by :mod:`mopidy.backends.spotify`.
#:
#: Default::
#:
#:     SPOTIFY_CACHE_PATH = u'$XDG_CACHE_DIR/mopidy/spotify'
SPOTIFY_CACHE_PATH = u'$XDG_CACHE_DIR/mopidy/spotify'

#: Your Spotify Premium username.
#:
#: Used by :mod:`mopidy.backends.spotify`.
SPOTIFY_USERNAME = u''

#: Your Spotify Premium password.
#:
#: Used by :mod:`mopidy.backends.spotify`.
SPOTIFY_PASSWORD = u''

#: Spotify preferred bitrate.
#:
#: Available values are 96, 160, and 320.
#:
#: Used by :mod:`mopidy.backends.spotify`.
#:
#: Default::
#:
#:     SPOTIFY_BITRATE = 160
SPOTIFY_BITRATE = 160
