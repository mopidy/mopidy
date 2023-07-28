from unittest import mock

import pytest

from mopidy import exceptions
from mopidy.internal import path

from tests import path_to_data_dir


@pytest.mark.parametrize(
    "track_uri", [path.path_to_uri(path_to_data_dir("song1.wav"))]
)
def test_lookup(provider, track_uri):
    result = provider.lookup(track_uri)

    assert len(result) == 1
    track = result[0]
    assert track.uri == track_uri
    assert track.length == 4406
    assert track.name == "song1.wav"

    with mock.patch(
        "mopidy.file.library.tags.convert_tags_to_track",
        side_effect=exceptions.ScannerError("test"),
    ):
        result = provider.lookup(track_uri)
        assert len(result) == 1
        track = result[0]
        assert track.uri == track_uri
        assert track.name == "song1.wav"
