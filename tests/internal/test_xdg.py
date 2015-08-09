from __future__ import unicode_literals

import os

import mock

import pytest

from mopidy.internal import xdg


@pytest.yield_fixture
def environ():
    patcher = mock.patch.dict(os.environ, clear=True)
    yield patcher.start()
    patcher.stop()


def test_cache_dir_default(environ):
    assert xdg.get_dirs()['XDG_CACHE_DIR'] == os.path.expanduser(b'~/.cache')


def test_cache_dir_from_env(environ):
    os.environ['XDG_CACHE_HOME'] = '/foo/bar'

    assert xdg.get_dirs()['XDG_CACHE_DIR'] == '/foo/bar'


def test_config_dir_default(environ):
    assert xdg.get_dirs()['XDG_CONFIG_DIR'] == os.path.expanduser(b'~/.config')


def test_config_dir_from_env(environ):
    os.environ['XDG_CONFIG_HOME'] = '/foo/bar'

    assert xdg.get_dirs()['XDG_CONFIG_DIR'] == '/foo/bar'


def test_data_dir_default(environ):
    assert xdg.get_dirs()['XDG_DATA_DIR'] == os.path.expanduser(
        b'~/.local/share')


def test_data_dir_from_env(environ):
    os.environ['XDG_DATA_HOME'] = '/foo/bar'

    assert xdg.get_dirs()['XDG_DATA_DIR'] == '/foo/bar'


def test_user_dirs(environ, tmpdir):
    os.environ['XDG_CONFIG_HOME'] = str(tmpdir)

    with open(os.path.join(str(tmpdir), 'user-dirs.dirs'), 'wb') as fh:
        fh.write('# Some comments\n')
        fh.write('XDG_MUSIC_DIR="$HOME/Music2"\n')

    result = xdg.get_dirs()

    assert result['XDG_MUSIC_DIR'] == os.path.expanduser(b'~/Music2')
    assert 'XDG_DOWNLOAD_DIR' not in result


def test_user_dirs_when_no_dirs_file(environ, tmpdir):
    os.environ['XDG_CONFIG_HOME'] = str(tmpdir)

    result = xdg.get_dirs()

    assert 'XDG_MUSIC_DIR' not in result
    assert 'XDG_DOWNLOAD_DIR' not in result
