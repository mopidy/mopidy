import shutil
from unittest import mock

import pytest

from mopidy._lib import paths
from mopidy._exts.file import backend
from mopidy.models import Ref
from tests import path_to_data_dir

SHEET = """\
REM DATE 2001
PERFORMER "Группа"
TITLE "Альбом"
FILE "album.flac" WAVE
  TRACK 01 AUDIO
    TITLE "Первый"
    INDEX 01 00:00:00
  TRACK 02 AUDIO
    TITLE "Второй"
    PERFORMER "Гость"
    INDEX 01 00:01:37
  TRACK 03 AUDIO
    TITLE "Третий"
    INDEX 01 00:03:00
"""


@pytest.fixture
def media_dirs(tmp_path):
    return [str(tmp_path)]


@pytest.fixture
def album_dir(tmp_path):
    shutil.copy(path_to_data_dir("song1.flac"), tmp_path / "album.flac")
    shutil.copy(path_to_data_dir("song2.flac"), tmp_path / "other.flac")
    (tmp_path / "album.cue").write_bytes(SHEET.encode("cp1251"))
    return tmp_path


@pytest.fixture
def cue_uri(album_dir):
    return paths.path_to_uri(album_dir / "album.cue")


@pytest.fixture
def config(config):
    config["file"]["cue_encodings"] = ["utf-8", "cp1251"]
    return config


def test_browse_shows_cue_sheet_as_directory_and_hides_its_audio(
    provider, album_dir, cue_uri
):
    result = provider.browse(paths.path_to_uri(album_dir))

    assert result == [
        Ref.directory(name="Альбом", uri=cue_uri),
        Ref.track(
            name="other.flac", uri=paths.path_to_uri(album_dir / "other.flac")
        ),
    ]


def test_browse_cue_sheet_lists_its_tracks(provider, cue_uri):
    result = provider.browse(cue_uri)

    assert result == [
        Ref.track(name="01 - Первый", uri=f"{cue_uri}#1"),
        Ref.track(name="02 - Второй", uri=f"{cue_uri}#2"),
        Ref.track(name="03 - Третий", uri=f"{cue_uri}#3"),
    ]


def test_browse_cue_track_is_rejected(provider, cue_uri, caplog):
    assert provider.browse(f"{cue_uri}#1") == []
    assert "Rejected attempt to browse track" in caplog.text


def test_browse_shows_a_broken_cue_sheet_as_a_file(provider, tmp_path):
    (tmp_path / "broken.cue").write_text("nonsense")
    (tmp_path / "song.flac").write_bytes(b"")

    result = provider.browse(paths.path_to_uri(tmp_path))

    assert [ref.name for ref in result] == ["broken.cue", "song.flac"]
    assert all(ref.type == Ref.TRACK for ref in result)


def test_browse_does_not_hide_files_if_the_cue_sheet_names_a_missing_file(
    provider, tmp_path
):
    (tmp_path / "song.flac").write_bytes(b"")
    (tmp_path / "album.cue").write_text(
        'FILE "gone.flac" WAVE\n TRACK 01 AUDIO\n  INDEX 01 00:00:00\n'
    )

    result = provider.browse(paths.path_to_uri(tmp_path))

    assert [ref.name for ref in result] == ["album.cue", "song.flac"]


def test_browse_with_cue_sheets_off_shows_files(config, album_dir):
    config["file"]["cue_sheets"] = False
    provider = backend.FileBackend(audio=mock.Mock(), config=config).library

    result = provider.browse(paths.path_to_uri(album_dir))

    assert [ref.name for ref in result] == ["album.cue", "album.flac", "other.flac"]


def test_lookup_cue_sheet_gives_all_tracks(provider, cue_uri):
    result = provider.lookup(cue_uri)

    assert [t.uri for t in result] == [f"{cue_uri}#1", f"{cue_uri}#2", f"{cue_uri}#3"]
    assert [t.name for t in result] == ["Первый", "Второй", "Третий"]
    assert [t.track_no for t in result] == [1, 2, 3]
    assert [t.length for t in result] == [1493, 1507, 1406]
    assert result[0].album.name == "Альбом"
    assert result[0].album.num_tracks == 3
    assert result[0].date == "2001"
    assert {a.name for a in result[0].artists} == {"Группа"}
    assert {a.name for a in result[1].artists} == {"Гость"}


def test_lookup_cue_track_gives_one_track(provider, cue_uri):
    result = provider.lookup(f"{cue_uri}#2")

    assert [t.name for t in result] == ["Второй"]
    assert result[0].uri == f"{cue_uri}#2"


@pytest.mark.parametrize("fragment", ["#0", "#4", "#x"])
def test_lookup_of_cue_track_that_does_not_exist(provider, cue_uri, fragment):
    assert provider.lookup(f"{cue_uri}{fragment}") == []
