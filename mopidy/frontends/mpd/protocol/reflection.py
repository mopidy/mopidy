from mopidy.frontends.mpd.protocol import handle_request, mpd_commands
from mopidy.frontends.mpd.exceptions import MpdNotImplemented

@handle_request(r'^commands$', auth_required=False)
def commands(context):
    """
    *musicpd.org, reflection section:*

        ``commands``

        Shows which commands the current user has access to.
    """
    if context.dispatcher.authenticated:
        command_names = set([command.name for command in mpd_commands])
    else:
        command_names = set([command.name for command in mpd_commands
            if not command.auth_required])

    # No one is permited to use kill, rest of commands are not listed by MPD,
    # so we shouldn't either.
    command_names = command_names - set(['kill', 'command_list_begin',
        'command_list_ok_begin', 'command_list_ok_begin', 'command_list_end',
        'idle', 'noidle', 'sticker'])

    return [('command', command_name) for command_name in sorted(command_names)]

@handle_request(r'^decoders$')
def decoders(context):
    """
    *musicpd.org, reflection section:*

        ``decoders``

        Print a list of decoder plugins, followed by their supported
        suffixes and MIME types. Example response::

            plugin: mad
            suffix: mp3
            suffix: mp2
            mime_type: audio/mpeg
            plugin: mpcdec
            suffix: mpc
    """
    raise MpdNotImplemented # TODO

@handle_request(r'^notcommands$', auth_required=False)
def notcommands(context):
    """
    *musicpd.org, reflection section:*

        ``notcommands``

        Shows which commands the current user does not have access to.
    """
    if context.dispatcher.authenticated:
        command_names = []
    else:
        command_names = [command.name for command in mpd_commands
            if command.auth_required]

    # No permission to use
    command_names.append('kill')

    return [('command', command_name) for command_name in sorted(command_names)]

@handle_request(r'^tagtypes$')
def tagtypes(context):
    """
    *musicpd.org, reflection section:*

        ``tagtypes``

        Shows a list of available song metadata.
    """
    pass # TODO

@handle_request(r'^urlhandlers$')
def urlhandlers(context):
    """
    *musicpd.org, reflection section:*

        ``urlhandlers``

        Gets a list of available URL handlers.
    """
    return [(u'handler', uri_scheme)
        for uri_scheme in context.backend.uri_schemes.get()]
