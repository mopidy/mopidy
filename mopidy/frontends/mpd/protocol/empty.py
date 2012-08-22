from mopidy.frontends.mpd.protocol import handle_request

@handle_request(r'^[ ]*$')
def empty(context):
    """The original MPD server returns ``OK`` on an empty request."""
    pass
