from mopidy.frontends.mpd.protocol import handle_request, mpd_commands
from mopidy.frontends.mpd.exceptions import MpdNotImplemented

@handle_request(r'^commands$')
def commands(context):
    """
    *musicpd.org, reflection section:*

        ``commands``

        Shows which commands the current user has access to.
    """
    # FIXME When password auth is turned on and the client is not
    # authenticated, 'commands' should list only the commands the client does
    # have access to. To implement this we need access to the session object to
    # check if the client is authenticated or not.

    command_names = [command.name for command in mpd_commands]

    # No permission to use
    command_names.remove('kill')

    # Not shown by MPD in its command list
    command_names.remove('command_list_begin')
    command_names.remove('command_list_ok_begin')
    command_names.remove('command_list_end')
    command_names.remove('idle')
    command_names.remove('noidle')
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

@handle_request(r'^notcommands$')
def notcommands(context):
    """
    *musicpd.org, reflection section:*

        ``notcommands``

        Shows which commands the current user does not have access to.
    """
    # FIXME When password auth is turned on and the client is not
    # authenticated, 'notcommands' should list all the commands the client does
    # not have access to. To implement this we need access to the session
    # object to check if the client is authenticated or not.

    command_names = []

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
    return [(u'handler', uri) for uri in context.backend.uri_handlers.get()]
