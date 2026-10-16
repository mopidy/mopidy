from unittest import mock

import pytest

from mopidy._exts.file import backend
from mopidy._lib import paths
from tests import path_to_data_dir


@pytest.fixture
def media_dirs(tmp_path):
    return [str(path_to_data_dir("")), str(tmp_path)]


@pytest.fixture
def provider(config):
    return backend.FileBackend(audio=mock.Mock(), config=config).playback


@pytest.fixture
def track_uri():
    return paths.path_to_uri(path_to_data_dir("song1.wav"))


def test_translate_uri_of_audio_file(provider, track_uri):
    assert provider.translate_uri(track_uri) == track_uri


def test_translate_uri_of_playlist_document(provider, tmp_path, track_uri):
    missing_uri = paths.path_to_uri(tmp_path / "no-such-file.ogg")
    playlist_path = tmp_path / "radio.pls"
    playlist_path.write_text(
        f"[playlist]\nNumberOfEntries=2\nFile1={missing_uri}\nFile2={track_uri}\n"
    )

    assert provider.translate_uri(paths.path_to_uri(playlist_path)) == track_uri


def test_translate_uri_of_file_that_cannot_be_read(provider, tmp_path):
    missing_uri = paths.path_to_uri(tmp_path / "no-such-file.ogg")

    assert provider.translate_uri(missing_uri) is None
