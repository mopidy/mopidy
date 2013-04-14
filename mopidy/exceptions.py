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


class ConfigError(MopidyException):
    def __init__(self, errors):
        self._errors = errors

    def __getitem__(self, key):
        return self._errors[key]

    def __iter__(self):
        return self._errors.iterkeys()

    @property
    def message(self):
        lines = []
        for key, msg in self._errors.items():
            lines.append('%s: %s' % (key, msg))
        return '\n'.join(lines)


class OptionalDependencyError(MopidyException):
    pass


class ExtensionError(MopidyException):
    pass
