from __future__ import unicode_literals

from subprocess import PIPE, Popen

from mopidy import __version__


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
