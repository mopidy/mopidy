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
        command_names = [command.name for command in mpd_commands]
    else:
        command_names = [command.name for command in mpd_commands
            if not command.auth_required]

    # No permission to use
    if 'kill' in command_names:
        command_names.remove('kill')

    # Not shown by MPD in its command list
    if 'command_list_begin' in command_names:
        command_names.remove('command_list_begin')
    if 'command_list_ok_begin' in command_names:
        command_names.remove('command_list_ok_begin')
    if 'command_list_end' in command_names:
        command_names.remove('command_list_end')
    if 'idle' in command_names:
        command_names.remove('idle')
    if 'noidle' in command_names:
        command_names.remove('noidle')
    if 'sticker' in command_names:
        command_names.remove('sticker')

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
