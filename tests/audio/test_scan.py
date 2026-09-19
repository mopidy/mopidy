import pytest

from mopidy import exceptions
from mopidy._lib.paths import path_to_uri
from mopidy.audio.scan import Scanner
from tests import path_to_data_dir


def find(path):
    dir_path = path_to_data_dir(path)
    if not dir_path.is_dir():
        return
    for file_path in dir_path.iterdir():
        yield dir_path / file_path


@pytest.fixture
def result():
    return {}


@pytest.fixture
def errors():
    return {}


@pytest.fixture
def scan(result, errors):
    def scan(paths):
        scanner = Scanner()
        for path in paths:
            uri = path_to_uri(path)
            try:
                result[path] = scanner.scan(uri)
            except exceptions.ScannerError as error:
                errors[path] = error

    return scan


def check(result, name, key, value):
    name = path_to_data_dir(name)
    assert result[name].tags[key] == value


def check_if_missing_plugin(result):
    for path, scan_result in result.items():
        if path.suffix != ".mp3":
            continue
        if not scan_result.playable and scan_result.mime == "audio/mpeg":
            msg = "Missing MP3 support?"
            pytest.skip(msg)


def test_tags_is_set(scan, result):
    scan(find("scanner/simple"))

    assert next(iter(result.values())).tags


def test_errors_is_not_set(scan, result, errors):
    scan(find("scanner/simple"))

    check_if_missing_plugin(result)

    assert not errors


def test_duration_is_set(scan, result):
    scan(find("scanner/simple"))

    check_if_missing_plugin(result)

    ogg = path_to_data_dir("scanner/simple/song1.ogg")
    mp3 = path_to_data_dir("scanner/simple/song1.mp3")
    assert result[mp3].duration == 4608
    assert result[ogg].duration == 4704


def test_artist_is_set(scan, result):
    scan(find("scanner/simple"))

    check_if_missing_plugin(result)

    check(result, "scanner/simple/song1.mp3", "artist", ["name"])
    check(result, "scanner/simple/song1.ogg", "artist", ["name"])


def test_album_is_set(scan, result):
    scan(find("scanner/simple"))

    check_if_missing_plugin(result)

    check(result, "scanner/simple/song1.mp3", "album", ["albumname"])
    check(result, "scanner/simple/song1.ogg", "album", ["albumname"])


def test_track_is_set(scan, result):
    scan(find("scanner/simple"))

    check_if_missing_plugin(result)

    check(result, "scanner/simple/song1.mp3", "title", ["trackname"])
    check(result, "scanner/simple/song1.ogg", "title", ["trackname"])


def test_nonexistent_dir_does_not_fail(scan, errors):
    scan(find("scanner/does-not-exist"))
    assert not errors


def test_other_media_is_ignored(scan, result):
    scan(find("scanner/image"))
    assert not next(iter(result.values())).playable


def test_log_file_that_gst_thinks_is_mpeg_1_is_ignored(scan, result):
    scan([path_to_data_dir("scanner/example.log")])

    check_if_missing_plugin(result)

    log = path_to_data_dir("scanner/example.log")
    assert result[log].duration is None


def test_empty_wav_file(scan, result):
    scan([path_to_data_dir("scanner/empty.wav")])
    wav = path_to_data_dir("scanner/empty.wav")
    assert result[wav].duration == 0


def test_uri_list(scan, result):
    path = path_to_data_dir("scanner/playlist.m3u")
    scan([path])
    assert result[path].mime == "text/uri-list"


def test_text_plain(scan, result, errors):
    # GStreamer either fails to typefind plain text at all, or, since
    # 1.28.5, types .txt as application/x-subtitle by extension.
    # Neither outcome is playable.
    path = path_to_data_dir("scanner/plain.txt")
    scan([path])
    assert path in errors or not result[path].playable


@pytest.mark.skip(reason="Not implemented")
def test_song_without_time_is_handeled():
    pass
