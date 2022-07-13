# TODO Test browse()
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
            "media_dirs": [str(path_to_data_dir(""))],
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


def test_file_browse(config, audio, track_uri, caplog):
    provider = backend.FileBackend(audio=audio, config=config).library
    result = provider.browse(track_uri)

    assert len(result) == 0
    assert any(map(lambda record: record.levelname == "ERROR", caplog.records))
    assert any(
        map(lambda record: "Rejected attempt" in record.message, caplog.records)
    )
