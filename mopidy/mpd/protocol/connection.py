from __future__ import absolute_import, unicode_literals

from mopidy.mpd import exceptions, protocol


@protocol.commands.add('close', auth_required=False)
def close(context):
    """
    *musicpd.org, connection section:*

        ``close``

        Closes the connection to MPD.
    """
    context.session.close()


@protocol.commands.add('kill', list_command=False)
def kill(context):
    """
    *musicpd.org, connection section:*

        ``kill``

        Kills MPD.
    """
    raise exceptions.MpdPermissionError(command='kill')


@protocol.commands.add('password', auth_required=False)
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
        raise exceptions.MpdPasswordError('incorrect password')


@protocol.commands.add('ping', auth_required=False)
def ping(context):
    """
    *musicpd.org, connection section:*

        ``ping``

        Does nothing but return ``OK``.
    """
    pass
