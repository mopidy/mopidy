import pytest

from mopidy._lib import paths
from tests import path_to_data_dir


@pytest.mark.parametrize(
    "track_uri",
    [
        paths.path_to_uri(path_to_data_dir("song1.wav")),
    ],
)
def test_lookup(provider, track_uri):
    result = provider.lookup(track_uri)

    assert len(result) == 1
    track = result[0]
    assert track.uri == track_uri
    assert track.length == 4406
    assert track.name == "song1.wav"


def test_lookup_of_file_with_tags(provider):
    track_uri = paths.path_to_uri(path_to_data_dir("scanner/simple/song1.ogg"))

    result = provider.lookup(track_uri)

    assert len(result) == 1
    track = result[0]
    assert track.uri == track_uri
    assert track.length == 4704
    assert track.name == "trackname"


def test_lookup_of_file_that_cannot_be_read(provider):
    track_uri = paths.path_to_uri(path_to_data_dir("no-such-file.ogg"))

    result = provider.lookup(track_uri)

    assert len(result) == 1
    track = result[0]
    assert track.uri == track_uri
    assert track.length is None
    assert track.name == "no-such-file.ogg"


@pytest.fixture
def media_dirs(tmp_path):
    return [str(path_to_data_dir("")), str(tmp_path)]


@pytest.fixture
def track_uri():
    return paths.path_to_uri(path_to_data_dir("song1.wav"))


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("radio.pls", "[playlist]\nNumberOfEntries=1\nFile1={track_uri}\n"),
        ("radio.m3u", "{track_uri}\n"),
        ("radio.m3u8", "#EXTM3U\n{track_uri}\n"),
        ("RADIO.PLS", "[playlist]\nNumberOfEntries=1\nFile1={track_uri}\n"),
        ("radio.txt", "[playlist]\nNumberOfEntries=1\nFile1={track_uri}\n"),
    ],
)
def test_lookup_of_playlist_document(provider, tmp_path, track_uri, filename, content):
    playlist_path = tmp_path / filename
    playlist_path.write_text(content.format(track_uri=track_uri))
    playlist_uri = paths.path_to_uri(playlist_path)

    result = provider.lookup(playlist_uri)

    assert len(result) == 1
    track = result[0]
    assert track.uri == playlist_uri
    assert track.length == 4406
    assert track.name == filename


def test_lookup_of_playlist_document_skips_entries_that_cannot_be_read(
    provider, tmp_path, track_uri
):
    missing_uri = paths.path_to_uri(tmp_path / "no-such-file.ogg")
    playlist_path = tmp_path / "radio.m3u"
    playlist_path.write_text(f"{missing_uri}\n{track_uri}\n")
    playlist_uri = paths.path_to_uri(playlist_path)

    result = provider.lookup(playlist_uri)

    assert len(result) == 1
    track = result[0]
    assert track.uri == playlist_uri
    assert track.length == 4406


def test_lookup_of_empty_playlist_document(provider, tmp_path):
    playlist_path = tmp_path / "empty.pls"
    playlist_path.write_text("")
    playlist_uri = paths.path_to_uri(playlist_path)

    result = provider.lookup(playlist_uri)

    assert len(result) == 1
    track = result[0]
    assert track.uri == playlist_uri
    assert track.length is None
    assert track.name == "empty.pls"
