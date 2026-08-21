import os
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


def test_user_dirs(environ, tmpdir):
    os.environ["XDG_CONFIG_HOME"] = str(tmpdir)

    with (Path(tmpdir) / "user-dirs.dirs").open("wb") as fh:
        fh.write(b"# Some comments\n")
        fh.write(b'XDG_MUSIC_DIR="$HOME/Music2"\n')

    result = paths.get_xdg_dirs()

    assert result["XDG_MUSIC_DIR"] == Path("~/Music2").expanduser()
    assert result["XDG_DOWNLOAD_DIR"] == Path("~/Downloads").expanduser()


def test_user_dirs_defaults_file_overrides_builtin_defaults(tmpdir):
    with (Path(tmpdir) / "user-dirs.defaults").open("w") as fh:
        fh.write("# Some comments\n")
        fh.write("MUSIC=Audio\n")
        fh.write("DOWNLOAD=Files\n")

    result = paths._get_xdg_user_dirs(
        xdg_config_dir=Path("/does/not/exist"),
        xdg_defaults_dir=Path(tmpdir),
    )

    assert result["XDG_MUSIC_DIR"] == Path("~/Audio").expanduser()
    assert result["XDG_DOWNLOAD_DIR"] == Path("~/Files").expanduser()


def test_user_dirs_defaults_file_ignores_absolute_paths(tmpdir):
    with (Path(tmpdir) / "user-dirs.defaults").open("w") as fh:
        fh.write("MUSIC=/srv/media\n")

    result = paths._get_xdg_user_dirs(
        xdg_config_dir=Path("/does/not/exist"),
        xdg_defaults_dir=Path(tmpdir),
    )

    assert result["XDG_MUSIC_DIR"] == Path("~/Music").expanduser()


def test_user_dirs_defaults_file_tolerates_whitespace_and_quotes(tmpdir):
    with (Path(tmpdir) / "user-dirs.defaults").open("w") as fh:
        fh.write(' MUSIC = "Audio Files"\n')

    result = paths._get_xdg_user_dirs(
        xdg_config_dir=Path("/does/not/exist"),
        xdg_defaults_dir=Path(tmpdir),
    )

    assert result["XDG_MUSIC_DIR"] == Path("~/Audio Files").expanduser()


def test_user_dirs_file_overrides_defaults_file(tmpdir):
    xdg_config_dir = Path(tmpdir) / "config"
    xdg_config_dir.mkdir()

    with (Path(tmpdir) / "user-dirs.defaults").open("w") as fh:
        fh.write("MUSIC=Audio\n")

    with (xdg_config_dir / "user-dirs.dirs").open("w") as fh:
        fh.write('XDG_MUSIC_DIR="$HOME/Music2"\n')

    result = paths._get_xdg_user_dirs(
        xdg_config_dir=xdg_config_dir,
        xdg_defaults_dir=Path(tmpdir),
    )

    assert result["XDG_MUSIC_DIR"] == Path("~/Music2").expanduser()


def test_user_dirs_file_accepts_reasonably_sourceable_value_forms(tmpdir):
    xdg_config_dir = Path(tmpdir) / "config"
    xdg_config_dir.mkdir()

    with (xdg_config_dir / "user-dirs.dirs").open("w") as fh:
        fh.write("XDG_MUSIC_DIR=$HOME/Music\n")
        fh.write(" XDG_DOWNLOAD_DIR = /srv/downloads\n")
        fh.write('XDG_PICTURES_DIR="/srv/pictures"\n')

    result = paths._read_xdg_user_dirs(xdg_config_dir / "user-dirs.dirs")

    assert result["XDG_MUSIC_DIR"] == Path("~/Music").expanduser()
    assert result["XDG_DOWNLOAD_DIR"] == Path("/srv/downloads")
    assert result["XDG_PICTURES_DIR"] == Path("/srv/pictures")


def test_user_dirs_file_ignores_unsupported_shell_forms(tmpdir):
    xdg_config_dir = Path(tmpdir) / "config"
    xdg_config_dir.mkdir()

    with (xdg_config_dir / "user-dirs.dirs").open("w") as fh:
        fh.write('XDG_MUSIC_DIR="$HOME"/Music\n')
        fh.write('XDG_DOWNLOAD_DIR="${HOME}/Downloads"\n')

    result = paths._read_xdg_user_dirs(xdg_config_dir / "user-dirs.dirs")

    assert "XDG_MUSIC_DIR" not in result
    assert "XDG_DOWNLOAD_DIR" not in result


def test_user_dirs_when_no_dirs_file(environ, tmpdir):
    os.environ["XDG_CONFIG_HOME"] = str(tmpdir)

    result = paths.get_xdg_dirs()

    assert result["XDG_MUSIC_DIR"] == Path("~/Music").expanduser()
    assert result["XDG_DOWNLOAD_DIR"] == Path("~/Downloads").expanduser()
