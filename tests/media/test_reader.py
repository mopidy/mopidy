from collections.abc import Iterator

import httpx
import pytest
from pytest_httpx import HTTPXMock

from mopidy._lib.paths import path_to_uri
from mopidy.config import Config
from mopidy.media import MediaReader, MediaReadError, PlaylistEntry
from mopidy.models import Track
from mopidy.types import DurationMs, Uri
from tests import path_to_data_dir

CONFIG = Config({"proxy": {}})


@pytest.fixture
def media_reader() -> Iterator[MediaReader]:
    with MediaReader.create(config=CONFIG, timeout=DurationMs(1000)) as media_reader:
        yield media_reader


class FakeMediaInfoReader:
    def __init__(self, results=None):
        self.results = results or {}

    def read_media_info(self, uri, *, timeout):
        result = self.results.get(uri, MediaReadError(f"Cannot read {uri}"))
        if isinstance(result, Exception):
            raise result
        return result


@pytest.fixture
def media_info_reader() -> FakeMediaInfoReader:
    return FakeMediaInfoReader()


@pytest.fixture
def fake_media_reader(media_info_reader: FakeMediaInfoReader) -> Iterator[MediaReader]:
    with MediaReader(
        media_info_reader=media_info_reader,
        timeout=DurationMs(1000),
    ) as media_reader:
        yield media_reader


class AudioStream(httpx.SyncByteStream):
    def __iter__(self):
        while True:
            yield b"\xff\xfb\x90\x00" * 1024


def entry(uri, name=None):
    return PlaylistEntry(track=Track(uri=uri, name=name), alternatives=(uri,))


def uri_of(name):
    return path_to_uri(path_to_data_dir(name))


def test_create_gives_a_reader_that_can_close():
    media_reader = MediaReader.create(config=CONFIG, timeout=DurationMs(1000))

    assert isinstance(media_reader, MediaReader)
    media_reader.close()


def test_create_uses_the_proxy_config(httpx_mock: HTTPXMock):
    config = Config({"proxy": {"hostname": "proxy.example.com", "port": 8080}})
    httpx_mock.add_response(
        url="http://example.com/radio.m3u",
        proxy_url="http://proxy.example.com:8080/",
        text="stream.mp3\n",
    )

    with MediaReader.create(config=config, timeout=DurationMs(1000)) as media_reader:
        media_reader.read_playlist_entries(Uri("http://example.com/radio.m3u"))

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["user-agent"].startswith("Mopidy/")


def test_reader_is_a_context_manager():
    with MediaReader.create(config=CONFIG, timeout=DurationMs(1000)) as media_reader:
        info = media_reader.read_media_info(uri_of("scanner/simple/song1.ogg"))

    assert info.playable is True


@pytest.mark.parametrize(
    ("name", "length"),
    [
        ("scanner/simple/song1.mp3", 4608),
        ("scanner/simple/song1.ogg", 4704),
    ],
)
def test_read_media_info_of_audio_file(media_reader, name, length):
    uri = uri_of(name)

    info = media_reader.read_media_info(uri)

    assert info.playable is True
    assert info.seekable is True
    assert info.track.uri == uri
    assert info.track.length == length
    assert info.track.name == "trackname"
    assert info.track.album is not None
    assert info.track.album.name == "albumname"
    assert [artist.name for artist in info.track.artists] == ["name"]


def test_read_media_info_of_flac_file_with_embedded_image(media_reader):
    uri = uri_of("scanner/embedded-image.flac")

    info = media_reader.read_media_info(uri)

    assert info.playable is True
    assert info.track.name == "embedded"
    assert info.track.length == 400
    assert [image.data for image in info.images] == [
        path_to_data_dir("scanner/image/test.png").read_bytes()
    ]


def test_read_media_info_of_text_file_is_not_playable(media_reader):
    try:
        info = media_reader.read_media_info(uri_of("scanner/plain.txt"))
    except MediaReadError:
        return

    assert info.playable is False


def test_read_media_info_of_missing_file_raises(media_reader):
    with pytest.raises(MediaReadError):
        media_reader.read_media_info(uri_of("scanner/no-such-file.ogg"))


def test_read_media_info_of_unknown_scheme_raises(media_reader):
    with pytest.raises(MediaReadError):
        media_reader.read_media_info("no-such-scheme:foo")


def test_read_media_info_raises_on_timeout(media_reader):
    with pytest.raises(MediaReadError, match="Timeout"):
        media_reader.read_media_info(
            uri_of("scanner/simple/song1.ogg"), timeout=DurationMs(0)
        )


def test_read_playlist_entries_over_http(fake_media_reader, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="http://example.com/radio.pls",
        text="[playlist]\nFile1=http://example.com/stream\nTitle1=Radio\n",
        headers={"content-type": "audio/x-scpls"},
    )

    entries = fake_media_reader.read_playlist_entries(
        Uri("http://example.com/radio.pls")
    )

    assert entries == (entry("http://example.com/stream", name="Radio"),)


def test_read_playlist_entries_joins_relative_entries_with_the_uri(
    fake_media_reader, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(url="http://example.com/a/radio.m3u", text="stream.mp3\n")

    entries = fake_media_reader.read_playlist_entries(
        Uri("http://example.com/a/radio.m3u")
    )

    assert entries == (entry("http://example.com/a/stream.mp3"),)


def test_read_playlist_entries_stops_reading_the_body_if_it_is_not_text(
    fake_media_reader, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        url="http://example.com/stream",
        stream=AudioStream(),
        headers={"content-type": "application/octet-stream"},
    )

    entries = fake_media_reader.read_playlist_entries(Uri("http://example.com/stream"))

    assert entries == ()


def test_read_playlist_entries_of_file(fake_media_reader, tmp_path):
    path = tmp_path / "radio.m3u"
    path.write_text("#EXTM3U\n#EXTINF:-1,Radio\nhttp://example.com/stream\n")

    entries = fake_media_reader.read_playlist_entries(path_to_uri(path))

    assert entries == (entry("http://example.com/stream", name="Radio"),)


def test_read_playlist_entries_of_missing_file_raises(fake_media_reader, tmp_path):
    with pytest.raises(MediaReadError):
        fake_media_reader.read_playlist_entries(path_to_uri(tmp_path / "missing.m3u"))


def test_read_playlist_entries_of_other_scheme_raises(fake_media_reader):
    with pytest.raises(MediaReadError, match="scheme 'rtsp'"):
        fake_media_reader.read_playlist_entries(Uri("rtsp://example.com/radio.m3u"))


def test_read_playlist_entries_raises_on_http_error_status(
    fake_media_reader, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(url="http://example.com/radio.m3u", status_code=404)

    with pytest.raises(MediaReadError, match="HTTP 404"):
        fake_media_reader.read_playlist_entries(Uri("http://example.com/radio.m3u"))


def test_read_playlist_entries_raises_when_the_connection_fails(
    fake_media_reader, httpx_mock: HTTPXMock
):
    httpx_mock.add_exception(httpx.ConnectError("Kaboom"))

    with pytest.raises(MediaReadError, match="Kaboom"):
        fake_media_reader.read_playlist_entries(Uri("http://example.com/radio.m3u"))


def test_read_playlist_entries_raises_on_timeout(
    fake_media_reader, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(url="http://example.com/radio.m3u", text="stream.mp3\n")

    with pytest.raises(MediaReadError, match="Timeout"):
        fake_media_reader.read_playlist_entries(
            Uri("http://example.com/radio.m3u"), timeout=DurationMs(0)
        )
