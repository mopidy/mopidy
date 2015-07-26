from __future__ import absolute_import, unicode_literals

from mopidy.mpd import exceptions, protocol
from mopidy.mpd.protocol import tagtype_list


@protocol.commands.add('config', list_command=False)
def config(context):
    """
    *musicpd.org, reflection section:*

        ``config``

        Dumps configuration values that may be interesting for the client. This
        command is only permitted to "local" clients (connected via UNIX domain
        socket).
    """
    raise exceptions.MpdPermissionError(command='config')


@protocol.commands.add('commands', auth_required=False)
def commands(context):
    """
    *musicpd.org, reflection section:*

        ``commands``

        Shows which commands the current user has access to.
    """
    command_names = set()
    for name, handler in protocol.commands.handlers.items():
        if not handler.list_command:
            continue
        if context.dispatcher.authenticated or not handler.auth_required:
            command_names.add(name)

    return [
        ('command', command_name) for command_name in sorted(command_names)]


@protocol.commands.add('decoders')
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

    *Clarifications:*

    - ncmpcpp asks for decoders the first time you open the browse view. By
      returning nothing and OK instead of an not implemented error, we avoid
      "Not implemented" showing up in the ncmpcpp interface, and we get the
      list of playlists without having to enter the browse interface twice.
    """
    return  # TODO


@protocol.commands.add('notcommands', auth_required=False)
def notcommands(context):
    """
    *musicpd.org, reflection section:*

        ``notcommands``

        Shows which commands the current user does not have access to.
    """
    command_names = set(['config', 'kill'])  # No permission to use
    for name, handler in protocol.commands.handlers.items():
        if not handler.list_command:
            continue
        if not context.dispatcher.authenticated and handler.auth_required:
            command_names.add(name)

    return [
        ('command', command_name) for command_name in sorted(command_names)]


@protocol.commands.add('tagtypes')
def tagtypes(context):
    """
    *musicpd.org, reflection section:*

        ``tagtypes``

        Shows a list of available song metadata.
    """
    return [
        ('tagtype', tagtype) for tagtype in tagtype_list.TAGTYPE_LIST
    ]


@protocol.commands.add('urlhandlers')
def urlhandlers(context):
    """
    *musicpd.org, reflection section:*

        ``urlhandlers``

        Gets a list of available URL handlers.
    """
    return [
        ('handler', uri_scheme)
        for uri_scheme in context.core.get_uri_schemes().get()]
