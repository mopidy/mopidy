from __future__ import unicode_literals

from mopidy.frontends.mpd.protocol import handle_request
from mopidy.frontends.mpd.exceptions import MpdNotImplemented


@handle_request(r'subscribe\ "(?P<channel>[A-Za-z0-9:._-]+)"$')
def subscribe(context, channel):
    """
    *musicpd.org, client to client section:*

        ``subscribe {NAME}``

        Subscribe to a channel. The channel is created if it does not exist
        already. The name may consist of alphanumeric ASCII characters plus
        underscore, dash, dot and colon.
    """
    raise MpdNotImplemented  # TODO


@handle_request(r'unsubscribe\ "(?P<channel>[A-Za-z0-9:._-]+)"$')
def unsubscribe(context, channel):
    """
    *musicpd.org, client to client section:*

        ``unsubscribe {NAME}``

        Unsubscribe from a channel.
    """
    raise MpdNotImplemented  # TODO


@handle_request(r'channels$')
def channels(context):
    """
    *musicpd.org, client to client section:*

        ``channels``

        Obtain a list of all channels. The response is a list of "channel:"
        lines.
    """
    raise MpdNotImplemented  # TODO


@handle_request(r'readmessages$')
def readmessages(context):
    """
    *musicpd.org, client to client section:*

        ``readmessages``

        Reads messages for this client. The response is a list of "channel:"
        and "message:" lines.
    """
    raise MpdNotImplemented  # TODO


@handle_request(
    r'sendmessage\ "(?P<channel>[A-Za-z0-9:._-]+)"\ "(?P<text>[^"]*)"$')
def sendmessage(context, channel, text):
    """
    *musicpd.org, client to client section:*

        ``sendmessage {CHANNEL} {TEXT}``

        Send a message to the specified channel.
    """
    raise MpdNotImplemented  # TODO
