import shutil
from unittest import mock

import pytest

from mopidy._exts.file import backend
from mopidy._lib import paths
from mopidy.models import Track
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


@pytest.fixture
def cue_uri(tmp_path):
    shutil.copy(path_to_data_dir("song1.flac"), tmp_path / "album.flac")
    (tmp_path / "album.cue").write_text(
        'FILE "album.flac" WAVE\n'
        '  TRACK 01 AUDIO\n    TITLE "A"\n    INDEX 01 00:00:00\n'
        '  TRACK 02 AUDIO\n    TITLE "B"\n    INDEX 01 00:01:00\n'
        '  TRACK 03 AUDIO\n    TITLE "C"\n    INDEX 01 00:03:00\n'
    )
    return paths.path_to_uri(tmp_path / "album.cue")


def test_translate_uri_of_cue_track_is_the_audio_file(provider, cue_uri, tmp_path):
    assert provider.translate_uri(f"{cue_uri}#2") == paths.path_to_uri(
        tmp_path / "album.flac"
    )


@pytest.mark.parametrize(
    ("position", "start", "end"),
    [(1, 0, 1000), (2, 1000, 3000), (3, 3000, None)],
)
def test_change_track_to_cue_track_plays_part_of_the_file(
    provider, cue_uri, tmp_path, position, start, end
):
    track = Track(uri=f"{cue_uri}#{position}")

    assert provider.change_track(track)

    provider.audio.set_uri.assert_called_once_with(
        paths.path_to_uri(tmp_path / "album.flac"), start=start, end=end
    )


@pytest.mark.parametrize("fragment", ["#9", "#x", ""])
def test_cue_track_that_does_not_exist_cannot_be_played(provider, cue_uri, fragment):
    uri = f"{cue_uri}{fragment}"

    assert provider.translate_uri(uri) is None
    assert not provider.change_track(Track(uri=uri))
    provider.audio.set_uri.assert_not_called()
