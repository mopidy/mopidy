import re

from mopidy import MopidyException

class MpdAckError(MopidyException):
    """
    Available MPD error codes::

        ACK_ERROR_NOT_LIST = 1
        ACK_ERROR_ARG = 2
        ACK_ERROR_PASSWORD = 3
        ACK_ERROR_PERMISSION = 4
        ACK_ERROR_UNKNOWN = 5
        ACK_ERROR_NO_EXIST = 50
        ACK_ERROR_PLAYLIST_MAX = 51
        ACK_ERROR_SYSTEM = 52
        ACK_ERROR_PLAYLIST_LOAD = 53
        ACK_ERROR_UPDATE_ALREADY = 54
        ACK_ERROR_PLAYER_SYNC = 55
        ACK_ERROR_EXIST = 56
    """

    def __init__(self, message=u'', error_code=0, index=0, command=u''):
        super(MpdAckError, self).__init__(message, error_code, index, command)
        self.message = message
        self.error_code = error_code
        self.index = index
        self.command = command

    def get_mpd_ack(self):
        """
        MPD error code format::

            ACK [%(error_code)i@%(index)i] {%(command)s} description
        """
        return u'ACK [%i@%i] {%s} %s' % (
            self.error_code, self.index, self.command, self.message)

class MpdArgError(MpdAckError):
    def __init__(self, *args, **kwargs):
        super(MpdArgError, self).__init__(*args, **kwargs)
        self.error_code = 2 # ACK_ERROR_ARG

class MpdUnknownCommand(MpdAckError):
    def __init__(self, *args, **kwargs):
        super(MpdUnknownCommand, self).__init__(*args, **kwargs)
        self.message = u'unknown command "%s"' % self.command
        self.command = u''
        self.error_code = 5 # ACK_ERROR_UNKNOWN

class MpdNoExistError(MpdAckError):
    def __init__(self, *args, **kwargs):
        super(MpdNoExistError, self).__init__(*args, **kwargs)
        self.error_code = 50 # ACK_ERROR_NO_EXIST

class MpdNotImplemented(MpdAckError):
    def __init__(self, *args, **kwargs):
        super(MpdNotImplemented, self).__init__(*args, **kwargs)
        self.message = u'Not implemented'

mpd_commands = set()
request_handlers = {}

def handle_pattern(pattern):
    """
    Decorator for connecting command handlers to command patterns.

    If you use named groups in the pattern, the decorated method will get the
    groups as keyword arguments. If the group is optional, remember to give the
    argument a default value.

    For example, if the command is ``do that thing`` the ``what`` argument will
    be ``this thing``::

        @handle_pattern('^do (?P<what>.+)$')
        def do(what):
            ...

    :param pattern: regexp pattern for matching commands
    :type pattern: string
    """
    def decorator(func):
        match = re.search('([a-z_]+)', pattern)
        if match is not None:
            mpd_commands.add(match.group())
        if pattern in request_handlers:
            raise ValueError(u'Tried to redefine handler for %s with %s' % (
                pattern, func))
        request_handlers[pattern] = func
        func.__doc__ = '        - **Pattern:** ``%s``\n\n%s' % (
            pattern, func.__doc__ or '')
        return func
    return decorator
