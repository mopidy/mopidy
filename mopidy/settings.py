"""
Available settings and their default values.

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

#: Which GStreamer bin description to use in
#: :class:`mopidy.outputs.custom.CustomOutput`.
#:
#: Default::
#:
#:     CUSTOM_OUTPUT = u'fakesink'
CUSTOM_OUTPUT = u'fakesink'

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
#:    # Defaults to asking glib where music is stored, fallback is ~/music
#:    LOCAL_MUSIC_PATH = None
LOCAL_MUSIC_PATH = None

#: Path to playlist folder with m3u files for local music.
#:
#: Used by :mod:`mopidy.backends.local`.
#:
#: Default::
#:
#:    LOCAL_PLAYLIST_PATH = None # Implies $XDG_DATA_DIR/mopidy/playlists
LOCAL_PLAYLIST_PATH = None

#: Path to tag cache for local music.
#:
#: Used by :mod:`mopidy.backends.local`.
#:
#: Default::
#:
#:    LOCAL_TAG_CACHE_FILE = None # Implies $XDG_DATA_DIR/mopidy/tag_cache
LOCAL_TAG_CACHE_FILE = None

#: Sound mixer to use. See :mod:`mopidy.mixers` for all available mixers.
#:
#: Default::
#:
#:     MIXER = u'mopidy.mixers.gstreamer_software.GStreamerSoftwareMixer'
MIXER = u'mopidy.mixers.gstreamer_software.GStreamerSoftwareMixer'

#: ALSA mixer only. What mixer control to use. If set to :class:`False`, first
#: ``Master`` and then ``PCM`` will be tried.
#:
#: Example: ``Master Front``. Default: :class:`False`
MIXER_ALSA_CONTROL = False

#: External mixers only. Which port the mixer is connected to.
#:
#: This must point to the device port like ``/dev/ttyUSB0``.
#:
#: Default: :class:`None`
MIXER_EXT_PORT = None

#: External mixers only. What input source the external mixer should use.
#:
#: Example: ``Aux``. Default: :class:`None`
MIXER_EXT_SOURCE = None

#: External mixers only. What state Speakers A should be in.
#:
#: Default: :class:`None`.
MIXER_EXT_SPEAKERS_A = None

#: External mixers only. What state Speakers B should be in.
#:
#: Default: :class:`None`.
MIXER_EXT_SPEAKERS_B = None

#: The maximum volume. Integer in the range 0 to 100.
#:
#: If this settings is set to 80, the mixer will set the actual volume to 80
#: when asked to set it to 100.
#:
#: Default::
#:
#:     MIXER_MAX_VOLUME = 100
MIXER_MAX_VOLUME = 100

#: Which address Mopidy's MPD server should bind to.
#:
#:Examples:
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
#: Default: 6600
MPD_SERVER_PORT = 6600

#: The password required for connecting to the MPD server.
#:
#: Default: :class:`None`, which means no password required.
MPD_SERVER_PASSWORD = None

#: The maximum number of concurrent connections the MPD server will accept.
#:
#: Default: 20
MPD_SERVER_MAX_CONNECTIONS = 20

#: List of outputs to use. See :mod:`mopidy.outputs` for all available
#: backends
#:
#: Default::
#:
#:     OUTPUTS = (
#:         u'mopidy.outputs.local.LocalOutput',
#:     )
OUTPUTS = (
    u'mopidy.outputs.local.LocalOutput',
)

#: Hostname of the SHOUTcast server which Mopidy should stream audio to.
#:
#: Used by :mod:`mopidy.outputs.shoutcast`.
#:
#: Default::
#:
#:    SHOUTCAST_OUTPUT_HOSTNAME = u'127.0.0.1'
SHOUTCAST_OUTPUT_HOSTNAME = u'127.0.0.1'

#: Port of the SHOUTcast server.
#:
#: Used by :mod:`mopidy.outputs.shoutcast`.
#:
#: Default::
#:
#:    SHOUTCAST_OUTPUT_PORT = 8000
SHOUTCAST_OUTPUT_PORT = 8000

#: User to authenticate as against SHOUTcast server.
#:
#: Used by :mod:`mopidy.outputs.shoutcast`.
#:
#: Default::
#:
#:    SHOUTCAST_OUTPUT_USERNAME = u'source'
SHOUTCAST_OUTPUT_USERNAME = u'source'

#: Password to authenticate with against SHOUTcast server.
#:
#: Used by :mod:`mopidy.outputs.shoutcast`.
#:
#: Default::
#:
#:    SHOUTCAST_OUTPUT_PASSWORD = u'hackme'
SHOUTCAST_OUTPUT_PASSWORD = u'hackme'

#: Mountpoint to use for the stream on the SHOUTcast server.
#:
#: Used by :mod:`mopidy.outputs.shoutcast`.
#:
#: Default::
#:
#:    SHOUTCAST_OUTPUT_MOUNT = u'/stream'
SHOUTCAST_OUTPUT_MOUNT = u'/stream'

#: Encoder to use to process audio data before streaming to SHOUTcast server.
#:
#: Used by :mod:`mopidy.outputs.shoutcast`.
#:
#: Default::
#:
#:     SHOUTCAST_OUTPUT_ENCODER = u'lame mode=stereo bitrate=320'
SHOUTCAST_OUTPUT_ENCODER = u'lame mode=stereo bitrate=320'

#: Path to the Spotify cache.
#:
#: Used by :mod:`mopidy.backends.spotify`.
SPOTIFY_CACHE_PATH = None

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
#
#: Default::
#:
#:     SPOTIFY_BITRATE = 160
SPOTIFY_BITRATE = 160
