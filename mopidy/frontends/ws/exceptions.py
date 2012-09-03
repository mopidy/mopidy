from mopidy import MopidyException

class WsAckError(MopidyException):
    """See fields on this class for available Ws error codes"""

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

    error_code = 0

    def __init__(self, message=u'', index=0, command=u''):
        super(WsAckError, self).__init__(message, index, command)
        self.message = message
        self.index = index
        self.command = command

    def get_ws_ack(self):
        """
        Ws error code format::

            ACK [%(error_code)i@%(index)i] {%(command)s} description
        """
        return u'ACK [%i@%i] {%s} %s' % (
            self.__class__.error_code, self.index, self.command, self.message)

class WsArgError(WsAckError):
    error_code = WsAckError.ACK_ERROR_ARG

class WsPasswordError(WsAckError):
    error_code = WsAckError.ACK_ERROR_PASSWORD

class WsPermissionError(WsAckError):
    error_code = WsAckError.ACK_ERROR_PERMISSION

    def __init__(self, *args, **kwargs):
        super(WsPermissionError, self).__init__(*args, **kwargs)
        self.message = u'you don\'t have permission for "%s"' % self.command

class WsUnknownCommand(WsAckError):
    error_code = WsAckError.ACK_ERROR_UNKNOWN

    def __init__(self, *args, **kwargs):
        super(WsUnknownCommand, self).__init__(*args, **kwargs)
        self.message = u'unknown command "%s"' % self.command
        self.command = u''

class WsNoExistError(WsAckError):
    error_code = WsAckError.ACK_ERROR_NO_EXIST

class WsSystemError(WsAckError):
    error_code = WsAckError.ACK_ERROR_SYSTEM

class WsNotImplemented(WsAckError):
    error_code = 0

    def __init__(self, *args, **kwargs):
        super(WsNotImplemented, self).__init__(*args, **kwargs)
        self.message = u'Not implemented'
