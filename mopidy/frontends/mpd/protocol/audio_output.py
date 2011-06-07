from mopidy.frontends.mpd.protocol import handle_request
from mopidy.frontends.mpd.exceptions import MpdNotImplemented

@handle_request(r'^disableoutput "(?P<outputid>\d+)"$')
def disableoutput(context, outputid):
    """
    *musicpd.org, audio output section:*

        ``disableoutput``

        Turns an output off.
    """
    raise MpdNotImplemented # TODO

@handle_request(r'^enableoutput "(?P<outputid>\d+)"$')
def enableoutput(context, outputid):
    """
    *musicpd.org, audio output section:*

        ``enableoutput``

        Turns an output on.
    """
    raise MpdNotImplemented # TODO

@handle_request(r'^outputs$')
def outputs(context):
    """
    *musicpd.org, audio output section:*

        ``outputs``

        Shows information about all outputs.
    """
    return [
        ('outputid', 0),
        ('outputname', None),
        ('outputenabled', 1),
    ]
