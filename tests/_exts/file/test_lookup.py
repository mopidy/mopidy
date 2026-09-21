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


def test_lookup_unwraps_pls_playlist(provider, tmp_path):
    pls_content = (
        "[playlist]\nNumberOfEntries=1\nFile1=http://stream.example.com/listen.pls\n"
    )
    pls_file = tmp_path / "test.pls"
    pls_file.write_text(pls_content)

    uri = f"file://{pls_file}"

    tracks = provider.lookup(uri)
    assert len(tracks) == 1
    assert tracks[0].uri == "http://stream.example.com/listen.pls"


def test_lookup_unwraps_m3u_playlist(provider, tmp_path):
    m3u_content = "http://stream.example.com/listen.mp3\n"
    m3u_file = tmp_path / "test.m3u"
    m3u_file.write_text(m3u_content)

    uri = f"file://{m3u_file}"

    tracks = provider.lookup(uri)
    assert len(tracks) == 1
    assert tracks[0].uri == "http://stream.example.com/listen.mp3"


def test_lookup_unwraps_uppercase_pls_extension(provider, tmp_path):
    pls_file = tmp_path / "TEST.PLS"
    pls_file.write_text(
        "[playlist]\nNumberOfEntries=1\nFile1=http://stream.example.com/listen.pls\n"
    )

    tracks = provider.lookup(f"file://{pls_file}")

    assert len(tracks) == 1
    assert tracks[0].uri == "http://stream.example.com/listen.pls"
