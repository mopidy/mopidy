class MopidyException(Exception):  # noqa: N818
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self._message = message

    @property
    def message(self):
        """Reimplement message field that was deprecated in Python 2.6."""
        return self._message

    @message.setter
    def message(self, message):
        self._message = message


class BackendError(MopidyException):
    pass


class CoreError(MopidyException):
    def __init__(self, message, errno=None):
        super().__init__(message, errno)
        self.errno = errno


class ExtensionError(MopidyException):
    pass


class FrontendError(MopidyException):
    pass


class MixerError(MopidyException):
    pass


class ScannerError(MopidyException):
    pass


class TracklistFull(CoreError):  # noqa: N818
    def __init__(self, message, errno=None):
        super().__init__(message, errno)
        self.errno = errno


class AudioException(MopidyException):
    pass


class ValidationError(ValueError):
    pass
