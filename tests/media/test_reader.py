from collections.abc import Iterator

import pytest

from mopidy._lib.paths import path_to_uri
from mopidy.config import Config
from mopidy.media import MediaReadError, Reader
from mopidy.types import DurationMs
from tests import path_to_data_dir

CONFIG = Config({"proxy": {}})


@pytest.fixture
def reader() -> Iterator[Reader]:
    with Reader.create(config=CONFIG, timeout=DurationMs(1000)) as reader:
        yield reader


def uri_of(name):
    return path_to_uri(path_to_data_dir(name))


def test_create_gives_a_reader_that_can_close():
    reader = Reader.create(config=CONFIG, timeout=DurationMs(1000))

    assert isinstance(reader, Reader)
    reader.close()


def test_reader_is_a_context_manager():
    with Reader.create(config=CONFIG, timeout=DurationMs(1000)) as reader:
        info = reader.read_media_info(uri_of("scanner/simple/song1.ogg"))

    assert info.playable is True


@pytest.mark.parametrize(
    ("name", "length"),
    [
        ("scanner/simple/song1.mp3", 4608),
        ("scanner/simple/song1.ogg", 4704),
    ],
)
def test_read_media_info_of_audio_file(reader, name, length):
    uri = uri_of(name)

    info = reader.read_media_info(uri)

    assert info.playable is True
    assert info.seekable is True
    assert info.track.uri == uri
    assert info.track.length == length
    assert info.track.name == "trackname"
    assert info.track.album is not None
    assert info.track.album.name == "albumname"
    assert [artist.name for artist in info.track.artists] == ["name"]


def test_read_media_info_of_flac_file_with_embedded_image(reader):
    uri = uri_of("scanner/embedded-image.flac")

    info = reader.read_media_info(uri)

    assert info.playable is True
    assert info.track.name == "embedded"
    assert info.track.length == 400
    assert [image.data for image in info.images] == [
        path_to_data_dir("scanner/image/test.png").read_bytes()
    ]


def test_read_media_info_of_text_file_is_not_playable(reader):
    try:
        info = reader.read_media_info(uri_of("scanner/plain.txt"))
    except MediaReadError:
        return

    assert info.playable is False


def test_read_media_info_of_missing_file_raises(reader):
    with pytest.raises(MediaReadError):
        reader.read_media_info(uri_of("scanner/no-such-file.ogg"))


def test_read_media_info_of_unknown_scheme_raises(reader):
    with pytest.raises(MediaReadError):
        reader.read_media_info("no-such-scheme:foo")


def test_read_media_info_raises_on_timeout():
    with (
        Reader.create(config=CONFIG, timeout=DurationMs(0)) as reader,
        pytest.raises(MediaReadError, match="Timeout"),
    ):
        reader.read_media_info(uri_of("scanner/simple/song1.ogg"))
