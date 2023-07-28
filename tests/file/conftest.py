from unittest import mock

import pytest

from mopidy.file import backend

from tests import path_to_data_dir


@pytest.fixture
def media_dirs():
    return [str(path_to_data_dir(""))]


@pytest.fixture
def follow_symlinks():
    return False


@pytest.fixture
def config(media_dirs, follow_symlinks):
    return {
        "proxy": {},
        "file": {
            "show_dotfiles": False,
            "media_dirs": media_dirs,
            "excluded_file_extensions": [".conf"],
            "follow_symlinks": follow_symlinks,
            "metadata_timeout": 1000,
        },
    }


@pytest.fixture
def provider(config):
    return backend.FileBackend(audio=mock.Mock(), config=config).library
