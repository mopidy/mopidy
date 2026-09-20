from unittest import mock

import pytest

from mopidy import exceptions
from mopidy._lib.paths import path_to_uri
from mopidy.audio import MediaKind, ScanResult
from mopidy.audio._gst.scan import GstScanData, GstScanner, _media_kind
from mopidy.types import DurationMs
from tests import path_to_data_dir


@pytest.fixture
def scanner():
    return GstScanner(timeout=DurationMs(1000))


def scan(scanner, name):
    return scanner.scan(path_to_uri(path_to_data_dir(name)))


def skip_if_missing_mp3(result):
    if not result.playable:
        pytest.skip("Missing MP3 support?")


@pytest.mark.parametrize(
    "name",
    ["scanner/simple/song1.mp3", "scanner/simple/song1.ogg"],
)
def test_scan_returns_a_track(scanner, name):
    result = scan(scanner, name)

    skip_if_missing_mp3(result)

    assert isinstance(result, ScanResult)
    assert result.track.name == "trackname"
    assert [artist.name for artist in result.track.artists] == ["name"]
    assert result.track.album is not None
    assert result.track.album.name == "albumname"


def test_track_uri_is_the_scanned_uri(scanner):
    name = "scanner/simple/song1.ogg"

    result = scan(scanner, name)

    assert result.uri == path_to_uri(path_to_data_dir(name))
    assert result.track.uri == result.uri


def test_duration_is_on_the_track(scanner):
    result = scan(scanner, "scanner/simple/song1.ogg")

    assert result.track.length == 4704


def test_audio_is_found(scanner):
    result = scan(scanner, "scanner/simple/song1.ogg")

    assert result.kind is MediaKind.AUDIO
    assert result.playable is True
    assert result.seekable is True


def test_image_is_neither_audio_nor_a_playlist(scanner):
    result = scan(scanner, "scanner/image/test.png")

    assert result.kind is MediaKind.OTHER
    assert result.playable is False
    assert result.track.length is None


def test_playlist_is_recognised(scanner):
    result = scan(scanner, "scanner/playlist.m3u")

    assert result.kind is MediaKind.PLAYLIST
    assert result.media_type == "text/uri-list"
    assert result.playable is False


@pytest.mark.parametrize(
    ("media_type", "has_audio", "expected"),
    [
        # A playlist type wins, even one named as audio.
        ("text/uri-list", False, MediaKind.PLAYLIST),
        ("application/xml", False, MediaKind.PLAYLIST),
        ("audio/x-mpegurl", False, MediaKind.PLAYLIST),
        # Decoded audio needs no media type. GStreamer often reports none.
        (None, True, MediaKind.AUDIO),
        # Recognised as media, even with nothing to decode it.
        ("audio/mpeg", False, MediaKind.AUDIO),
        ("video/quicktime", False, MediaKind.AUDIO),
        ("application/ogg", False, MediaKind.AUDIO),
        # Neither.
        ("image/png", False, MediaKind.OTHER),
        (None, False, MediaKind.OTHER),
    ],
)
def test_media_kind(media_type, has_audio, expected):
    assert _media_kind(media_type, has_audio=has_audio) is expected


def test_missing_file_raises_scanner_error(scanner):
    with pytest.raises(exceptions.ScannerError):
        scanner.scan("file:///nonexistent-mopidy-test-file")


def test_scan_uses_the_default_timeout(scanner, mocker):
    scan_uri = mocker.patch("mopidy.audio._gst.scan.scan_uri")
    scan_uri.return_value = GstScanData(
        tags={}, duration=None, seekable=False, mime=None, has_audio=False
    )

    scan(scanner, "scanner/simple/song1.ogg")

    assert scan_uri.call_args.kwargs["timeout_ms"] == 1000


def test_per_call_timeout_overrides_the_default(scanner, mocker):
    scan_uri = mocker.patch("mopidy.audio._gst.scan.scan_uri")
    scan_uri.return_value = GstScanData(
        tags={}, duration=None, seekable=False, mime=None, has_audio=False
    )
    uri = path_to_uri(path_to_data_dir("scanner/simple/song1.ogg"))

    scanner.scan(uri, timeout=DurationMs(1234))

    assert scan_uri.call_args.kwargs["timeout_ms"] == 1234


def test_invalid_tags_are_dropped_but_the_scan_stands(scanner):
    """One bad tag costs the tags, not the whole scan."""
    with mock.patch(
        "mopidy.audio._gst.scan.tags_lib.convert_tags_to_track",
        side_effect=exceptions.ScannerError("test"),
    ):
        result = scan(scanner, "scanner/simple/song1.ogg")

    assert result.track.name is None
    assert result.track.length == 4704
    assert result.playable is True
