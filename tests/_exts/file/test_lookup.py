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
