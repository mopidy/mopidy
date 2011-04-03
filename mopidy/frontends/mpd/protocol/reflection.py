from mopidy.frontends.mpd.protocol import handle_pattern, mpd_commands
from mopidy.frontends.mpd.exceptions import MpdNotImplemented

@handle_pattern(r'^commands$')
def commands(frontend):
    """
    *musicpd.org, reflection section:*

        ``commands``

        Shows which commands the current user has access to.
    """
    # FIXME When password auth is turned on and the client is not
    # authenticated, 'commands' should list only the commands the client does
    # have access to. To implement this we need access to the session object to
    # check if the client is authenticated or not.

    sorted_commands = sorted(list(mpd_commands))

    # Not shown by MPD in its command list
    sorted_commands.remove('command_list_begin')
    sorted_commands.remove('command_list_ok_begin')
    sorted_commands.remove('command_list_end')
    sorted_commands.remove('idle')
    sorted_commands.remove('noidle')
    sorted_commands.remove('sticker')

    return [('command', c) for c in sorted_commands]

@handle_pattern(r'^decoders$')
def decoders(frontend):
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

@handle_pattern(r'^notcommands$')
def notcommands(frontend):
    """
    *musicpd.org, reflection section:*

        ``notcommands``

        Shows which commands the current user does not have access to.
    """
    # FIXME When password auth is turned on and the client is not
    # authenticated, 'notcommands' should list all the commands the client does
    # not have access to. To implement this we need access to the session
    # object to check if the client is authenticated or not.
    pass

@handle_pattern(r'^tagtypes$')
def tagtypes(frontend):
    """
    *musicpd.org, reflection section:*

        ``tagtypes``

        Shows a list of available song metadata.
    """
    pass # TODO

@handle_pattern(r'^urlhandlers$')
def urlhandlers(frontend):
    """
    *musicpd.org, reflection section:*

        ``urlhandlers``

        Gets a list of available URL handlers.
    """
    return [(u'handler', uri) for uri in frontend.backend.uri_handlers.get()]
