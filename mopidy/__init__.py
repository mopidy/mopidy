import platform
import sys
if not (2, 6) <= sys.version_info < (3,):
    sys.exit(u'Mopidy requires Python >= 2.6, < 3')

import glib
import os

from subprocess import PIPE, Popen

VERSION = (0, 7, 0)

DATA_PATH = os.path.join(str(glib.get_user_data_dir()), 'mopidy')
CACHE_PATH = os.path.join(str(glib.get_user_cache_dir()), 'mopidy')
SETTINGS_PATH = os.path.join(str(glib.get_user_config_dir()), 'mopidy')
SETTINGS_FILE = os.path.join(SETTINGS_PATH, 'settings.py')

def get_version():
    try:
        return get_git_version()
    except EnvironmentError:
        return get_plain_version()

def get_git_version():
    process = Popen(['git', 'describe'], stdout=PIPE, stderr=PIPE)
    if process.wait() != 0:
        raise EnvironmentError('Execution of "git describe" failed')
    version = process.stdout.read().strip()
    if version.startswith('v'):
        version = version[1:]
    return version

def get_plain_version():
    return '.'.join(map(str, VERSION))

def get_platform():
    return platform.platform()

def get_python():
    implementation = platform.python_implementation()
    version = platform.python_version()
    return u' '.join([implementation, version])

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
