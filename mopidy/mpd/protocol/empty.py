from __future__ import unicode_literals

from mopidy.mpd.protocol import handle_request
from mopidy.mpd.exceptions import MpdNoCommand


@handle_request(r'[\ ]*$')
def empty(context):
    """The original MPD server returns an error on an empty request."""
    raise MpdNoCommand()
