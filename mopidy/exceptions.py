from __future__ import unicode_literals


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


class ExtensionError(MopidyException):
    pass


class ScannerError(MopidyException):
    pass
