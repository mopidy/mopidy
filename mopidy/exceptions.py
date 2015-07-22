from __future__ import absolute_import, unicode_literals


class MopidyException(Exception):

    def __init__(self, message, *args, **kwargs):
        super(MopidyException, self).__init__(message, *args, **kwargs)
        self._message = message

    @property
    def message(self):
        """Reimplement message field that was deprecated in Python 2.6"""
        return self._message

    @message.setter  # noqa
    def message(self, message):
        self._message = message


class BackendError(MopidyException):
    pass


class CoreError(MopidyException):

    def __init__(self, message, errno=None):
        super(CoreError, self).__init__(message, errno)
        self.errno = errno


class ExtensionError(MopidyException):
    pass


class FindError(MopidyException):

    def __init__(self, message, errno=None):
        super(FindError, self).__init__(message, errno)
        self.errno = errno


class FrontendError(MopidyException):
    pass


class MixerError(MopidyException):
    pass


class ScannerError(MopidyException):
    pass


class TracklistFull(CoreError):

    def __init__(self, message, errno=None):
        super(TracklistFull, self).__init__(message, errno)
        self.errno = errno


class AudioException(MopidyException):
    pass


class ValidationError(ValueError):
    pass
