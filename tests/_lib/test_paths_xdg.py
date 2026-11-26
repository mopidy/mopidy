import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from mopidy._lib import paths


@pytest.fixture
def environ():
    patcher = mock.patch.dict(os.environ, clear=True)
    yield patcher.start()
    patcher.stop()


def test_cache_dir_default(environ):
    assert paths.get_xdg_dirs()["XDG_CACHE_DIR"] == Path("~/.cache").expanduser()


def test_cache_dir_from_env(environ):
    os.environ["XDG_CACHE_HOME"] = "/foo/bar"

    assert paths.get_xdg_dirs()["XDG_CACHE_DIR"] == Path("/foo/bar")


def test_config_dir_default(environ):
    assert paths.get_xdg_dirs()["XDG_CONFIG_DIR"] == Path("~/.config").expanduser()


def test_config_dir_from_env(environ):
    os.environ["XDG_CONFIG_HOME"] = "/foo/bar"

    assert paths.get_xdg_dirs()["XDG_CONFIG_DIR"] == Path("/foo/bar")


def test_data_dir_default(environ):
    assert paths.get_xdg_dirs()["XDG_DATA_DIR"] == Path("~/.local/share").expanduser()


def test_data_dir_from_env(environ):
    os.environ["XDG_DATA_HOME"] = "/foo/bar"

    assert paths.get_xdg_dirs()["XDG_DATA_DIR"] == Path("/foo/bar")


def test_user_dirs(environ):
    # platformdirs ignores user-dirs.dirs if another user owns one of its parent
    # dirs. In CI, another user owns the checkout that has the pytest tmpdir.
    with tempfile.TemporaryDirectory(dir="/tmp") as config_dir:
        os.environ["XDG_CONFIG_HOME"] = config_dir

        user_dirs = Path(config_dir) / "user-dirs.dirs"
        with user_dirs.open("wb") as fh:
            fh.write(b"# Some comments\n")
            fh.write(b'XDG_MUSIC_DIR="$HOME/Music2"\n')
        # platformdirs also ignores the file if other users can write to it.
        user_dirs.chmod(0o600)

        result = paths.get_xdg_dirs()

    assert result["XDG_MUSIC_DIR"] == Path("~/Music2").expanduser()
    assert result["XDG_DOWNLOAD_DIR"] == Path("~/Downloads").expanduser()


def test_user_dirs_when_no_dirs_file(environ, tmpdir):
    os.environ["XDG_CONFIG_HOME"] = str(tmpdir)

    result = paths.get_xdg_dirs()

    assert result["XDG_MUSIC_DIR"] == Path("~/Music").expanduser()
    assert result["XDG_DOWNLOAD_DIR"] == Path("~/Downloads").expanduser()
