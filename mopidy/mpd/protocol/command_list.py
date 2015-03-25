from __future__ import absolute_import, unicode_literals

from mopidy.mpd import exceptions, protocol


@protocol.commands.add('command_list_begin', list_command=False)
def command_list_begin(context):
    """
    *musicpd.org, command list section:*

        To facilitate faster adding of files etc. you can pass a list of
        commands all at once using a command list. The command list begins
        with ``command_list_begin`` or ``command_list_ok_begin`` and ends
        with ``command_list_end``.

        It does not execute any commands until the list has ended. The
        return value is whatever the return for a list of commands is. On
        success for all commands, ``OK`` is returned. If a command fails,
        no more commands are executed and the appropriate ``ACK`` error is
        returned. If ``command_list_ok_begin`` is used, ``list_OK`` is
        returned for each successful command executed in the command list.
    """
    context.dispatcher.command_list_receiving = True
    context.dispatcher.command_list_ok = False
    context.dispatcher.command_list = []


@protocol.commands.add('command_list_end', list_command=False)
def command_list_end(context):
    """See :meth:`command_list_begin()`."""
    # TODO: batch consecutive add commands
    if not context.dispatcher.command_list_receiving:
        raise exceptions.MpdUnknownCommand(command='command_list_end')
    context.dispatcher.command_list_receiving = False
    (command_list, context.dispatcher.command_list) = (
        context.dispatcher.command_list, [])
    (command_list_ok, context.dispatcher.command_list_ok) = (
        context.dispatcher.command_list_ok, False)
    command_list_response = []
    for index, command in enumerate(command_list):
        response = context.dispatcher.handle_request(
            command, current_command_list_index=index)
        command_list_response.extend(response)
        if (command_list_response and
                command_list_response[-1].startswith('ACK')):
            return command_list_response
        if command_list_ok:
            command_list_response.append('list_OK')
    return command_list_response


@protocol.commands.add('command_list_ok_begin', list_command=False)
def command_list_ok_begin(context):
    """See :meth:`command_list_begin()`."""
    context.dispatcher.command_list_receiving = True
    context.dispatcher.command_list_ok = True
    context.dispatcher.command_list = []
