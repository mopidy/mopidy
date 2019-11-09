from unittest import mock

import pytest

from mopidy.file import backend
from mopidy.internal import path

from tests import path_to_data_dir


@pytest.fixture
def config():
    return {
        "proxy": {},
        "file": {
            "show_dotfiles": False,
            "media_dirs": [],
            "excluded_file_extensions": [],
            "follow_symlinks": False,
            "metadata_timeout": 1000,
        },
    }


@pytest.fixture
def audio():
    return mock.Mock()


@pytest.fixture
def track_uri():
    return path.path_to_uri(path_to_data_dir("song1.wav"))


def test_lookup(config, audio, track_uri):
    provider = backend.FileBackend(audio=audio, config=config).library

    result = provider.lookup(track_uri)

    assert len(result) == 1
    track = result[0]
    assert track.uri == track_uri
    assert track.length == 4406
    assert track.name == "song1.wav"
