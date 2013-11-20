from __future__ import unicode_literals

from mopidy.frontends.mpd.exceptions import MpdNoExistError
from mopidy.frontends.mpd.protocol import handle_request


@handle_request(r'disableoutput\ "(?P<outputid>\d+)"$')
def disableoutput(context, outputid):
    """
    *musicpd.org, audio output section:*

        ``disableoutput``

        Turns an output off.
    """
    if int(outputid) == 0:
        context.core.playback.set_mute(False)
    else:
        raise MpdNoExistError('No such audio output', command='disableoutput')


@handle_request(r'enableoutput\ "(?P<outputid>\d+)"$')
def enableoutput(context, outputid):
    """
    *musicpd.org, audio output section:*

        ``enableoutput``

        Turns an output on.
    """
    if int(outputid) == 0:
        context.core.playback.set_mute(True)
    else:
        raise MpdNoExistError('No such audio output', command='enableoutput')


@handle_request(r'outputs$')
def outputs(context):
    """
    *musicpd.org, audio output section:*

        ``outputs``

        Shows information about all outputs.
    """
    muted = 1 if context.core.playback.get_mute().get() else 0
    return [
        ('outputid', 0),
        ('outputname', 'Mute'),
        ('outputenabled', muted),
    ]
