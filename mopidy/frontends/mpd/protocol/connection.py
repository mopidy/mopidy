from mopidy import settings
from mopidy.frontends.mpd.protocol import handle_pattern
from mopidy.frontends.mpd.exceptions import (MpdPasswordError,
    MpdPermissionError)

@handle_pattern(r'^close$')
def close(context):
    """
    *musicpd.org, connection section:*

        ``close``

        Closes the connection to MPD.
    """
    context.session.close()

@handle_pattern(r'^kill$')
def kill(context):
    """
    *musicpd.org, connection section:*

        ``kill``

        Kills MPD.
    """
    raise MpdPermissionError(command=u'kill')

@handle_pattern(r'^password "(?P<password>[^"]+)"$')
def password_(context, password):
    """
    *musicpd.org, connection section:*

        ``password {PASSWORD}``

        This is used for authentication with the server. ``PASSWORD`` is
        simply the plaintext password.
    """
    # You will not get to this code without being authenticated. This is for
    # when you are already authenticated, and are sending additional 'password'
    # requests.
    if settings.MPD_SERVER_PASSWORD != password:
        raise MpdPasswordError(u'incorrect password', command=u'password')

@handle_pattern(r'^ping$')
def ping(context):
    """
    *musicpd.org, connection section:*

        ``ping``

        Does nothing but return ``OK``.
    """
    pass
