from __future__ import unicode_literals

from mopidy.mpd.protocol import handle_request


@handle_request(r'[\ ]*$')
def empty(context):
    """The original MPD server returns ``OK`` on an empty request."""
    pass
