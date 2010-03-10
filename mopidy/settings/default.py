"""
Available settings and their default values.

.. warning::

    Do *not* change settings here. Instead, add a file called
    ``mopidy/settings/local.py`` and redefine settings there.
"""

import sys

#: List of playback backends to use. Default::
#:
#:     BACKENDS = (u'mopidy.backends.despotify.DespotifyBackend',)
#:
#: .. note::
#:     Currently only the first backend in the list is used.
BACKENDS = (
    u'mopidy.backends.despotify.DespotifyBackend',
    #u'mopidy.backends.libspotify.LibspotifyBackend',
)

#: The log format used on the console. See
#: http://docs.python.org/library/logging.html#formatter-objects for details on
#: the format.
CONSOLE_LOG_FORMAT = u'%(levelname)-8s %(asctime)s [%(threadName)s] %(name)s\n  %(message)s'

#: Sound mixer to use.
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
#:
#: **Available external mixers**
#:
#: .. note::
#:     Using external mixers depends on the pyserial library.
#:
#: Denon AVR/AVC via RS-232::
#:
#:     MIXER = u'mopidy.mixers.denon.DenonMixer'
#:
MIXER = u'mopidy.mixers.dummy.DummyMixer'
if sys.platform == 'linux2':
    MIXER = u'mopidy.mixers.alsa.AlsaMixer'
elif sys.platform == 'darwin':
    MIXER = u'mopidy.mixers.osa.OsaMixer'

#: Which port a mixer is connected to if using an external mixer.
#: This must point to the device port like ``/dev/ttyUSB0`` or similar.
MIXER_PORT = None

#: Which address Mopidy should bind to. Examples:
#:
#: ``localhost``
#:     Listens only on the loopback interface. *Default.*
#: ``0.0.0.0``
#:     Listens on all interfaces.
MPD_SERVER_HOSTNAME = u'localhost'

#: Which TCP port Mopidy should listen to. *Default: 6600*
MPD_SERVER_PORT = 6600

#: Your Spotify Premium username. Used by all Spotify backends.
SPOTIFY_USERNAME = u''

#: Your Spotify Premium password. Used by all Spotify backends.
SPOTIFY_PASSWORD = u''
