"""
Available settings and their default values.

.. warning::

    Do *not* change settings here. Instead, add a file called
    ``mopidy/settings/local.py`` and redefine settings there.
"""

#: List of playback backends to use. Default::
#:
#:     BACKENDS = (u'mopidy.backends.despotify.DespotifyBackend',)
#:
#: .. note::
#:     Currently only the first backend in the list is used.
#:
BACKENDS = (
    u'mopidy.backends.despotify.DespotifyBackend',
    #u'mopidy.backends.libspotify.LibspotifyBackend',
)

#: The log format used on the console. See
#: http://docs.python.org/library/logging.html#formatter-objects for details on
#: the format.
CONSOLE_LOG_FORMAT = u'%(levelname)-8s %(asctime)s [%(threadName)s] %(name)s\n  %(message)s'

#: Which address Mopidy should bind to. Examples:
#:
#: ``localhost``
#:     Listens only on the loopback interface. *Default.*
#: ``0.0.0.0``
#:     listens on all interfaces.
MPD_SERVER_HOSTNAME = u'localhost'

#: Which TCP port Mopidy should listen to. *Default: 6600*
MPD_SERVER_PORT = 6600

#: Your Spotify Premium username. Used by all Spotify backends.
SPOTIFY_USERNAME = u''

#: Your Spotify Premium password. Used by all Spotify backends.
SPOTIFY_PASSWORD = u''
