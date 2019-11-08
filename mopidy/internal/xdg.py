import configparser
import os
import pathlib


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
        "XDG_CACHE_DIR": pathlib.Path(
            os.getenv("XDG_CACHE_HOME", "~/.cache")
        ).expanduser(),
        "XDG_CONFIG_DIR": pathlib.Path(
            os.getenv("XDG_CONFIG_HOME", "~/.config")
        ).expanduser(),
        "XDG_DATA_DIR": pathlib.Path(
            os.getenv("XDG_DATA_HOME", "~/.local/share")
        ).expanduser(),
    }

    dirs.update(_get_user_dirs(dirs["XDG_CONFIG_DIR"]))

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

    dirs_file = xdg_config_dir / "user-dirs.dirs"

    if not dirs_file.exists():
        return {}

    data = dirs_file.read_bytes()
    data = b"[XDG_USER_DIRS]\n" + data
    data = data.replace(b"$HOME", bytes(pathlib.Path.home()))
    data = data.replace(b'"', b"")

    config = configparser.RawConfigParser()
    config.read_string(data.decode())

    result = {}
    for k, v in config.items("XDG_USER_DIRS"):
        if v is None:
            continue
        if isinstance(k, bytes):
            k = k.decode()
        result[k.upper()] = pathlib.Path(v).resolve()

    return result
