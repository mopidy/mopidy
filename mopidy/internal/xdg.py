from __future__ import absolute_import, unicode_literals

import io
import os

from mopidy.compat import configparser


def get_dirs():
    """Returns a dict of all the known XDG Base Directories for the current user.

    The keys ``XDG_CACHE_DIR``, ``XDG_CONFIG_DIR``, and ``XDG_DATA_DIR`` is
    always available.

    Additional keys, like ``XDG_MUSIC_DIR``, may be available if the
    ``$XDG_CONFIG_DIR/user-dirs.dirs`` file exists and is parseable.

    See http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html
    for the XDG Base Directory specification.
    """

    dirs = {
        'XDG_CACHE_DIR': (
            os.environ.get('XDG_CACHE_HOME') or
            os.path.expanduser(b'~/.cache')),
        'XDG_CONFIG_DIR': (
            os.environ.get('XDG_CONFIG_HOME') or
            os.path.expanduser(b'~/.config')),
        'XDG_DATA_DIR': (
            os.environ.get('XDG_DATA_HOME') or
            os.path.expanduser(b'~/.local/share')),
    }

    dirs.update(_get_user_dirs(dirs['XDG_CONFIG_DIR']))

    return dirs


def _get_user_dirs(xdg_config_dir):
    """Returns a dict of XDG dirs read from
    ``$XDG_CONFIG_HOME/user-dirs.dirs``.

    This is used at import time for most users of :mod:`mopidy`. By rolling our
    own implementation instead of using :meth:`glib.get_user_special_dir` we
    make it possible for many extensions to run their test suites, which are
    importing parts of :mod:`mopidy`, in a virtualenv with global site-packages
    disabled, and thus no :mod:`glib` available.
    """

    dirs_file = os.path.join(xdg_config_dir, b'user-dirs.dirs')

    if not os.path.exists(dirs_file):
        return {}

    with open(dirs_file, 'rb') as fh:
        data = fh.read().decode('utf-8')

    data = '[XDG_USER_DIRS]\n' + data
    data = data.replace('$HOME', os.path.expanduser('~'))
    data = data.replace('"', '')

    config = configparser.RawConfigParser()
    config.readfp(io.StringIO(data))

    return {
        k.upper(): os.path.abspath(v)
        for k, v in config.items('XDG_USER_DIRS') if v is not None}
