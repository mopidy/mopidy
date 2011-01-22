import sys
if not (2, 6) <= sys.version_info < (3,):
    sys.exit(u'Mopidy requires Python >= 2.6, < 3')

def get_version():
    return u'0.3.0'

class MopidyException(Exception):
    def __init__(self, message, *args, **kwargs):
        super(MopidyException, self).__init__(message, *args, **kwargs)
        self._message = message

    @property
    def message(self):
        """Reimplement message field that was deprecated in Python 2.6"""
        return self._message

    @message.setter
    def message(self, message):
        self._message = message

class SettingsError(MopidyException):
    pass

class OptionalDependencyError(MopidyException):
    pass

from mopidy import settings as default_settings_module
from mopidy.utils.settings import SettingsProxy
settings = SettingsProxy(default_settings_module)
