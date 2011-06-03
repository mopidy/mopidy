from mopidy.frontends.mpd.protocol import handle_pattern

@handle_pattern(r'^$')
def empty(context):
    """The original MPD server returns ``OK`` on an empty request."""
    pass
