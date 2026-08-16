from unittest import mock

import pytest

from mopidy import exceptions
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

    with mock.patch(
        "mopidy._exts.file.library.tags.convert_tags_to_track",
        side_effect=exceptions.ScannerError("test"),
    ):
        result = provider.lookup(track_uri)
        assert len(result) == 1
        track = result[0]
        assert track.uri == track_uri
        assert track.name == "song1.wav"


def test_lookup_with_invalid_tags(provider):
    """A file with tags we can't validate is still listed, just without tags."""
    track_uri = paths.path_to_uri(path_to_data_dir("song1.wav"))
    real_scan = provider._scanner.scan

    def scan_with_invalid_tags(uri, *args, **kwargs):
        result = real_scan(uri, *args, **kwargs)
        return result._replace(tags=result.tags | {"track-number": [-1]})

    with mock.patch.object(
        provider._scanner,
        "scan",
        side_effect=scan_with_invalid_tags,
    ):
        result = provider.lookup(track_uri)

    assert len(result) == 1
    assert result[0].uri == track_uri
    assert result[0].name == "song1.wav"
    assert result[0].track_no is None
