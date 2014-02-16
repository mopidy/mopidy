from __future__ import unicode_literals

from mopidy.mpd.protocol import handle_request
from mopidy.mpd.exceptions import (
    MpdPasswordError, MpdPermissionError)


@handle_request(r'close$', auth_required=False)
def close(context):
    """
    *musicpd.org, connection section:*

        ``close``

        Closes the connection to MPD.
    """
    context.session.close()


@handle_request(r'kill$')
def kill(context):
    """
    *musicpd.org, connection section:*

        ``kill``

        Kills MPD.
    """
    raise MpdPermissionError(command='kill')


@handle_request(r'password\ "(?P<password>[^"]+)"$', auth_required=False)
def password(context, password):
    """
    *musicpd.org, connection section:*

        ``password {PASSWORD}``

        This is used for authentication with the server. ``PASSWORD`` is
        simply the plaintext password.
    """
    if password == context.password:
        context.dispatcher.authenticated = True
    else:
        raise MpdPasswordError('incorrect password')


@handle_request(r'ping$', auth_required=False)
def ping(context):
    """
    *musicpd.org, connection section:*

        ``ping``

        Does nothing but return ``OK``.
    """
    pass
