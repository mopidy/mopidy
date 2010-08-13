"""
Available settings and their default values.

.. warning::

    Do *not* change settings directly in :mod:`mopidy.settings`. Instead, add a
    file called ``~/.mopidy/settings.py`` and redefine settings there.
"""

# Absolute import needed to import ~/.mopidy/settings.py and not ourselves
from __future__ import absolute_import
import os
import sys

#: List of playback backends to use. See :mod:`mopidy.backends` for all
#: available backends.
#:
#: Default::
#:
#:     BACKENDS = (u'mopidy.backends.libspotify.LibspotifyBackend',)
#:
#: .. note::
#:     Currently only the first backend in the list is used.
BACKENDS = (
    u'mopidy.backends.libspotify.LibspotifyBackend',
)

#: The log format used on the console. See
#: http://docs.python.org/library/logging.html#formatter-objects for details on
#: the format.
CONSOLE_LOG_FORMAT = u'%(levelname)-8s %(asctime)s' + \
    ' [%(process)d:%(threadName)s] %(name)s\n  %(message)s'

#: The log format used for dump logs.
#:
#: Default::
#:
#:     DUMP_LOG_FILENAME = CONSOLE_LOG_FORMAT
DUMP_LOG_FORMAT = CONSOLE_LOG_FORMAT

#: The file to dump debug log data to when Mopidy is run with the
#: :option:`--dump` option.
#:
#: Default::
#:
#:     DUMP_LOG_FILENAME = u'dump.log'
DUMP_LOG_FILENAME = u'dump.log'

#: Protocol frontend to use.
#:
#: Default::
#:
#:     FRONTEND = u'mopidy.frontends.mpd.frontend.MpdFrontend'
FRONTEND = u'mopidy.frontends.mpd.frontend.MpdFrontend'

#: Path to folder with local music.
#:
#: Used by :mod:`mopidy.backends.local`.
#:
#: Default::
#:
#:    LOCAL_MUSIC_FOLDER = u'~/music'
LOCAL_MUSIC_FOLDER = u'~/music'

#: Path to playlist folder with m3u files for local music.
#:
#: Used by :mod:`mopidy.backends.local`.
#:
#: Default::
#:
#:    LOCAL_PLAYLIST_FOLDER = u'~/.mopidy/playlists'
LOCAL_PLAYLIST_FOLDER = u'~/.mopidy/playlists'

#: Path to tag cache for local music.
#:
#: Used by :mod:`mopidy.backends.local`.
#:
#: Default::
#:
#:    LOCAL_TAG_CACHE = u'~/.mopidy/tag_cache'
LOCAL_TAG_CACHE = u'~/.mopidy/tag_cache'

#: Sound mixer to use. See :mod:`mopidy.mixers` for all available mixers.
#:
#: Default on Linux::
#:
#:     MIXER = u'mopidy.mixers.alsa.AlsaMixer'
#:
#: Default on OS X::
#:
#:     MIXER = u'mopidy.mixers.osa.OsaMixer'
#:
#: Default on other operating systems::
#:
#:     MIXER = u'mopidy.mixers.dummy.DummyMixer'
MIXER = u'mopidy.mixers.dummy.DummyMixer'
if sys.platform == 'linux2':
    MIXER = u'mopidy.mixers.alsa.AlsaMixer'
elif sys.platform == 'darwin':
    MIXER = u'mopidy.mixers.osa.OsaMixer'

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

#: Audio output handler to use.
#:
#: Default::
#:
#:     OUTPUT = u'mopidy.outputs.gstreamer.GStreamerOutput'
OUTPUT = u'mopidy.outputs.gstreamer.GStreamerOutput'

#: Server to use.
#:
#: Default::
#:
#:     SERVER = u'mopidy.frontends.mpd.server.MpdServer'
SERVER = u'mopidy.frontends.mpd.server.MpdServer'

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

#: Path to your libspotify application key.
#:
#: Used by :mod:`mopidy.backends.libspotify`.
SPOTIFY_LIB_APPKEY = u'~/.mopidy/spotify_appkey.key'

#: Path to the libspotify cache.
#:
#: Used by :mod:`mopidy.backends.libspotify`.
SPOTIFY_LIB_CACHE = u'~/.mopidy/libspotify_cache'

#: Your Spotify Premium username.
#:
#: Used by :mod:`mopidy.backends.libspotify`.
SPOTIFY_USERNAME = u''

#: Your Spotify Premium password.
#:
#: Used by :mod:`mopidy.backends.libspotify`.
SPOTIFY_PASSWORD = u''

# Import user specific settings
dotdir = os.path.expanduser(u'~/.mopidy/')
settings_file = os.path.join(dotdir, u'settings.py')
if os.path.isfile(settings_file):
    sys.path.insert(0, dotdir)
    from settings import *
