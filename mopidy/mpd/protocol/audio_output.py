from __future__ import unicode_literals

from mopidy.mpd import exceptions, protocol


@protocol.commands.add('disableoutput', outputid=protocol.UINT)
def disableoutput(context, outputid):
    """
    *musicpd.org, audio output section:*

        ``disableoutput``

        Turns an output off.
    """
    if outputid == 0:
        context.core.playback.set_mute(False)
    else:
        raise exceptions.MpdNoExistError('No such audio output')


@protocol.commands.add('enableoutput', outputid=protocol.UINT)
def enableoutput(context, outputid):
    """
    *musicpd.org, audio output section:*

        ``enableoutput``

        Turns an output on.
    """
    if outputid == 0:
        context.core.playback.set_mute(True)
    else:
        raise exceptions.MpdNoExistError('No such audio output')


@protocol.commands.add('outputs')
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
