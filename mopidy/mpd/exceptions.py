from __future__ import absolute_import, unicode_literals

from mopidy.exceptions import MopidyException


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

    def __init__(self, message='', index=0, command=None):
        super(MpdAckError, self).__init__(message, index, command)
        self.message = message
        self.index = index
        self.command = command

    def get_mpd_ack(self):
        """
        MPD error code format::

            ACK [%(error_code)i@%(index)i] {%(command)s} description
        """
        return 'ACK [%i@%i] {%s} %s' % (
            self.__class__.error_code, self.index, self.command, self.message)


class MpdArgError(MpdAckError):
    error_code = MpdAckError.ACK_ERROR_ARG


class MpdPasswordError(MpdAckError):
    error_code = MpdAckError.ACK_ERROR_PASSWORD


class MpdPermissionError(MpdAckError):
    error_code = MpdAckError.ACK_ERROR_PERMISSION

    def __init__(self, *args, **kwargs):
        super(MpdPermissionError, self).__init__(*args, **kwargs)
        assert self.command is not None, 'command must be given explicitly'
        self.message = 'you don\'t have permission for "%s"' % self.command


class MpdUnknownError(MpdAckError):
    error_code = MpdAckError.ACK_ERROR_UNKNOWN


class MpdUnknownCommand(MpdUnknownError):

    def __init__(self, *args, **kwargs):
        super(MpdUnknownCommand, self).__init__(*args, **kwargs)
        assert self.command is not None, 'command must be given explicitly'
        self.message = 'unknown command "%s"' % self.command
        self.command = ''


class MpdNoCommand(MpdUnknownCommand):

    def __init__(self, *args, **kwargs):
        kwargs['command'] = ''
        super(MpdNoCommand, self).__init__(*args, **kwargs)
        self.message = 'No command given'


class MpdNoExistError(MpdAckError):
    error_code = MpdAckError.ACK_ERROR_NO_EXIST


class MpdExistError(MpdAckError):
    error_code = MpdAckError.ACK_ERROR_EXIST


class MpdSystemError(MpdAckError):
    error_code = MpdAckError.ACK_ERROR_SYSTEM


class MpdInvalidPlaylistName(MpdAckError):
    error_code = MpdAckError.ACK_ERROR_ARG

    def __init__(self, *args, **kwargs):
        super(MpdInvalidPlaylistName, self).__init__(*args, **kwargs)
        self.message = ('playlist name is invalid: playlist names may not '
                        'contain slashes, newlines or carriage returns')


class MpdNotImplemented(MpdAckError):
    error_code = 0

    def __init__(self, *args, **kwargs):
        super(MpdNotImplemented, self).__init__(*args, **kwargs)
        self.message = 'Not implemented'


class MpdInvalidTrackForPlaylist(MpdAckError):
    # NOTE: This is a custom error for Mopidy that does not exist in MPD.
    error_code = 0

    def __init__(self, playlist_scheme, track_scheme, *args, **kwargs):
        super(MpdInvalidTrackForPlaylist, self).__init__(*args, **kwargs)
        self.message = (
            'Playlist with scheme "%s" can\'t store track scheme "%s"' %
            (playlist_scheme, track_scheme))


class MpdFailedToSavePlaylist(MpdAckError):
    # NOTE: This is a custom error for Mopidy that does not exist in MPD.
    error_code = 0

    def __init__(self, backend_scheme, *args, **kwargs):
        super(MpdFailedToSavePlaylist, self).__init__(*args, **kwargs)
        self.message = 'Backend with scheme "%s" failed to save playlist' % (
            backend_scheme)


class MpdDisabled(MpdAckError):
    # NOTE: This is a custom error for Mopidy that does not exist in MPD.
    error_code = 0

    def __init__(self, *args, **kwargs):
        super(MpdDisabled, self).__init__(*args, **kwargs)
        assert self.command is not None, 'command must be given explicitly'
        self.message = '"%s" has been disabled in the server' % self.command
