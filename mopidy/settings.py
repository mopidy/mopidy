CONSOLE_LOG_FORMAT = u'%(levelname)-8s %(asctime)s %(name)s\n  %(message)s'
MPD_LINE_ENCODING = u'utf-8'
MPD_LINE_TERMINATOR = u'\n'
MPD_SERVER_HOSTNAME = u'localhost'
MPD_SERVER_PORT = 6600

SPOTIFY_USERNAME = ''
SPOTIFY_PASSWORD = ''

try:
    from mopidy.local_settings import *
except ImportError:
    pass
