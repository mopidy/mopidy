import os
import sys
if not (2, 6) <= sys.version_info < (3,):
    sys.exit(u'Mopidy requires Python >= 2.6, < 3')

VERSION = (0, 4, 0)

def is_in_git_repo():
    git_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../.git'))
    return os.path.exists(git_dir)

def get_git_version():
    if not is_in_git_repo():
        return None
    git_version = os.popen('git describe').read().strip()
    if git_version.startswith('v'):
        git_version = git_version[1:]
    return git_version

def get_plain_version():
    return '.'.join(map(str, VERSION))

def get_version():
    if is_in_git_repo():
        return get_git_version()
    else:
        return get_plain_version()

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
