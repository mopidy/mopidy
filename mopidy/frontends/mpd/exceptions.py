from mopidy import MopidyException

class MpdAckError(MopidyException):
    """See fields on this class for available MPD error codes"""

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
        super(MpdAckError, self).__init__(message, index, command)
        self.message = message
        self.index = index
        self.command = command

    def get_mpd_ack(self):
        """
        MPD error code format::

            ACK [%(error_code)i@%(index)i] {%(command)s} description
        """
        return u'ACK [%i@%i] {%s} %s' % (
            self.__class__.error_code, self.index, self.command, self.message)

class MpdArgError(MpdAckError):
    error_code = MpdAckError.ACK_ERROR_ARG

class MpdPasswordError(MpdAckError):
    error_code = MpdAckError.ACK_ERROR_PASSWORD

class MpdPermissionError(MpdAckError):
    error_code = MpdAckError.ACK_ERROR_PERMISSION

    def __init__(self, *args, **kwargs):
        super(MpdPermissionError, self).__init__(*args, **kwargs)
        self.message = u'you don\'t have permission for "%s"' % self.command

class MpdUnknownCommand(MpdAckError):
    error_code = MpdAckError.ACK_ERROR_UNKNOWN

    def __init__(self, *args, **kwargs):
        super(MpdUnknownCommand, self).__init__(*args, **kwargs)
        self.message = u'unknown command "%s"' % self.command
        self.command = u''

class MpdNoExistError(MpdAckError):
    error_code = MpdAckError.ACK_ERROR_NO_EXIST

class MpdSystemError(MpdAckError):
    error_code = MpdAckError.ACK_ERROR_SYSTEM

class MpdNotImplemented(MpdAckError):
    error_code = 0

    def __init__(self, *args, **kwargs):
        super(MpdNotImplemented, self).__init__(*args, **kwargs)
        self.message = u'Not implemented'
