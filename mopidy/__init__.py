import sys
if not (2, 6) <= sys.version_info < (3,):
    sys.exit(u'Mopidy requires Python >= 2.6, < 3')

from distutils.version import StrictVersion
import os
import platform
from subprocess import PIPE, Popen

import glib

import pykka
if StrictVersion(pykka.__version__) < StrictVersion('0.16'):
    sys.exit(u'Mopidy requires Pykka >= 0.16')

__version__ = '0.8.0'

DATA_PATH = os.path.join(str(glib.get_user_data_dir()), 'mopidy')
CACHE_PATH = os.path.join(str(glib.get_user_cache_dir()), 'mopidy')
SETTINGS_PATH = os.path.join(str(glib.get_user_config_dir()), 'mopidy')
SETTINGS_FILE = os.path.join(SETTINGS_PATH, 'settings.py')


def get_version():
    try:
        return get_git_version()
    except EnvironmentError:
        return __version__


def get_git_version():
    process = Popen(['git', 'describe'], stdout=PIPE, stderr=PIPE)
    if process.wait() != 0:
        raise EnvironmentError('Execution of "git describe" failed')
    version = process.stdout.read().strip()
    if version.startswith('v'):
        version = version[1:]
    return version


def get_platform():
    return platform.platform()


def get_python():
    implementation = platform.python_implementation()
    version = platform.python_version()
    return u' '.join([implementation, version])


from mopidy import settings as default_settings_module
from mopidy.utils.settings import SettingsProxy
settings = SettingsProxy(default_settings_module)
