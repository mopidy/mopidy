"""
Available settings and their default values.

.. warning::

    Do *not* change settings in ``mopidy/settings/default.py``. Instead, add a
    file called ``mopidy/settings/local.py`` and redefine settings there.
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

#: External mixers only. Which port the mixer is connected to.
#:
#: This must point to the device port like ``/dev/ttyUSB0``.
#: *Default:* :class:`None`
MIXER_EXT_PORT = None

#: External mixers only. What input source the external mixer should use.
#:
#: Example: ``Aux``. *Default:* :class:`None`
MIXER_EXT_SOURCE = None

#: External mixers only. What state Speakers A should be in.
#:
#: *Default:* :class:`None`.
MIXER_EXT_SPEAKERS_A = None

#: External mixers only. What state Speakers B should be in.
#:
#: *Default:* :class:`None`.
MIXER_EXT_SPEAKERS_B = None

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
