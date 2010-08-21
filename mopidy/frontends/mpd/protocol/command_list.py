from mopidy.frontends.mpd.protocol import handle_pattern
from mopidy.frontends.mpd.exceptions import MpdUnknownCommand

@handle_pattern(r'^command_list_begin$')
def command_list_begin(frontend):
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
    frontend.command_list = []
    frontend.command_list_ok = False

@handle_pattern(r'^command_list_end$')
def command_list_end(frontend):
    """See :meth:`command_list_begin()`."""
    if frontend.command_list is False:
        # Test for False exactly, and not e.g. empty list
        raise MpdUnknownCommand(command='command_list_end')
    (command_list, frontend.command_list) = (frontend.command_list, False)
    (command_list_ok, frontend.command_list_ok) = (
        frontend.command_list_ok, False)
    result = []
    for i, command in enumerate(command_list):
        response = frontend.handle_request(command, command_list_index=i)
        if response is not None:
            result.append(response)
        if response and response[-1].startswith(u'ACK'):
            return result
        if command_list_ok:
            response.append(u'list_OK')
    return result

@handle_pattern(r'^command_list_ok_begin$')
def command_list_ok_begin(frontend):
    """See :meth:`command_list_begin()`."""
    frontend.command_list = []
    frontend.command_list_ok = True
