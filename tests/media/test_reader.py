from collections.abc import Iterator

import httpx
import pytest
from pytest_httpx import HTTPXMock

from mopidy._lib.paths import path_to_uri
from mopidy.config import Config
from mopidy.media import (
    MediaInfo,
    MediaReader,
    MediaReadError,
    PlaybackTarget,
    PlaylistEntry,
)
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
        self.uris = []

    def read_media_info(self, uri, *, timeout):
        self.uris.append(uri)
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


def entry(uri, name=None):
    return PlaylistEntry(track=Track(uri=uri, name=name), alternatives=(uri,))


class AudioStream(httpx.SyncByteStream):
    def __iter__(self):
        while True:
            yield b"\xff\xfb\x90\x00" * 1024


def playable(uri):
    return MediaInfo(track=Track(uri=uri), playable=True, seekable=False)


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


def test_find_playback_target_of_playable_uri(fake_media_reader, media_info_reader):
    media_info_reader.results["rtsp://example.com/stream"] = playable(
        "rtsp://example.com/stream"
    )

    target = fake_media_reader.find_playback_target(Uri("rtsp://example.com/stream"))

    assert target == PlaybackTarget(
        uri="rtsp://example.com/stream",
        info=playable("rtsp://example.com/stream"),
        entry=None,
    )


def test_find_playback_target_stops_reading_the_body_if_it_is_not_text(
    fake_media_reader, media_info_reader, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        url="http://example.com/stream",
        stream=AudioStream(),
        headers={"content-type": "application/octet-stream"},
    )
    media_info_reader.results["http://example.com/stream"] = playable(
        "http://example.com/stream"
    )

    target = fake_media_reader.find_playback_target(Uri("http://example.com/stream"))

    assert target is not None
    assert target.info == playable("http://example.com/stream")


def test_find_playback_target_tries_the_next_entry(
    fake_media_reader, media_info_reader, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        url="http://example.com/radio.pls",
        text=(
            "[playlist]\n"
            "File1=http://down.example.com/stream\n"
            "File2=http://up.example.com/stream\n"
        ),
        headers={"content-type": "audio/x-scpls"},
    )
    httpx_mock.add_exception(
        httpx.ConnectError("Kaboom"), url="http://down.example.com/stream"
    )
    httpx_mock.add_response(
        url="http://up.example.com/stream",
        headers={"content-type": "audio/mpeg"},
    )
    media_info_reader.results["http://up.example.com/stream"] = playable(
        "http://up.example.com/stream"
    )

    target = fake_media_reader.find_playback_target(Uri("http://example.com/radio.pls"))

    assert target == PlaybackTarget(
        uri="http://up.example.com/stream",
        info=playable("http://up.example.com/stream"),
        entry=entry("http://up.example.com/stream"),
    )


def test_find_playback_target_tries_the_next_alternative(
    fake_media_reader, media_info_reader, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        url="http://example.com/radio.xspf",
        text=(
            '<playlist version="1" xmlns="http://xspf.org/ns/0/"><trackList>'
            "<track>"
            "<location>http://down.example.com/stream</location>"
            "<location>http://up.example.com/stream</location>"
            "</track>"
            "</trackList></playlist>"
        ),
        headers={"content-type": "application/xspf+xml"},
    )
    httpx_mock.add_response(url="http://down.example.com/stream", status_code=503)
    httpx_mock.add_response(
        url="http://up.example.com/stream",
        headers={"content-type": "audio/mpeg"},
    )
    media_info_reader.results["http://up.example.com/stream"] = playable(
        "http://up.example.com/stream"
    )

    target = fake_media_reader.find_playback_target(
        Uri("http://example.com/radio.xspf")
    )

    assert target is not None
    assert target.uri == "http://up.example.com/stream"
    assert target.entry is not None
    assert target.entry.alternatives == (
        "http://down.example.com/stream",
        "http://up.example.com/stream",
    )


def test_find_playback_target_goes_into_nested_playlist_documents(
    fake_media_reader, media_info_reader, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        url="http://example.com/radio.pls",
        text="[playlist]\nFile1=http://example.com/radio.m3u\n",
    )
    httpx_mock.add_response(
        url="http://example.com/radio.m3u",
        text="#EXTM3U\n#EXTINF:-1,Radio\nhttp://example.com/stream\n",
    )
    httpx_mock.add_response(
        url="http://example.com/stream",
        headers={"content-type": "audio/mpeg"},
    )
    media_info_reader.results["http://example.com/stream"] = playable(
        "http://example.com/stream"
    )

    target = fake_media_reader.find_playback_target(Uri("http://example.com/radio.pls"))

    assert target == PlaybackTarget(
        uri="http://example.com/stream",
        info=playable("http://example.com/stream"),
        entry=entry("http://example.com/stream", name="Radio"),
    )


def test_find_playback_target_skips_a_uri_that_was_tried_before(
    fake_media_reader, media_info_reader, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        url="http://example.com/radio.m3u",
        text="#EXTM3U\nhttp://example.com/radio.m3u\nhttp://example.com/stream\n",
        is_reusable=True,
    )
    httpx_mock.add_response(
        url="http://example.com/stream",
        headers={"content-type": "audio/mpeg"},
    )
    media_info_reader.results["http://example.com/stream"] = playable(
        "http://example.com/stream"
    )

    target = fake_media_reader.find_playback_target(Uri("http://example.com/radio.m3u"))

    assert target is not None
    assert target.uri == "http://example.com/stream"
    assert len(httpx_mock.get_requests(url="http://example.com/radio.m3u")) == 1


def test_find_playback_target_stops_at_the_deadline(
    media_info_reader, httpx_mock: HTTPXMock, mocker
):
    httpx_mock.add_response(
        url="http://example.com/radio.m3u",
        text="#EXTM3U\nhttp://example.com/a\nhttp://example.com/b\n",
    )
    monotonic = mocker.patch("time.monotonic", return_value=0)

    def pass_the_deadline(request):
        monotonic.return_value = 10
        raise httpx.ConnectError(request=request, message="Kaboom")

    httpx_mock.add_callback(pass_the_deadline, url="http://example.com/a")

    with MediaReader(
        media_info_reader=media_info_reader, timeout=DurationMs(1000)
    ) as media_reader:
        target = media_reader.find_playback_target(Uri("http://example.com/radio.m3u"))

    assert target is None
    assert [str(request.url) for request in httpx_mock.get_requests()] == [
        "http://example.com/radio.m3u",
        "http://example.com/a",
    ]


def test_find_playback_target_reads_media_info_of_hls(
    fake_media_reader, media_info_reader, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        url="http://example.com/radio.m3u8",
        text="#EXTM3U\n#EXT-X-TARGETDURATION:10\n#EXTINF:10,\nsegment1.aac\n",
        headers={"content-type": "application/vnd.apple.mpegurl"},
    )
    media_info_reader.results["http://example.com/radio.m3u8"] = playable(
        "http://example.com/radio.m3u8"
    )

    target = fake_media_reader.find_playback_target(
        Uri("http://example.com/radio.m3u8")
    )

    assert target == PlaybackTarget(
        uri="http://example.com/radio.m3u8",
        info=playable("http://example.com/radio.m3u8"),
        entry=None,
    )


def test_find_playback_target_reads_media_info_of_file_that_is_not_a_playlist(
    fake_media_reader, media_info_reader
):
    uri = uri_of("song1.wav")
    media_info_reader.results[uri] = playable(uri)

    target = fake_media_reader.find_playback_target(uri)

    assert target == PlaybackTarget(uri=uri, info=playable(uri), entry=None)


def test_find_playback_target_reads_media_info_if_the_fetch_fails(
    fake_media_reader, media_info_reader, httpx_mock: HTTPXMock
):
    httpx_mock.add_exception(
        httpx.RemoteProtocolError("illegal status line: bytearray(b'ICY 200 OK')"),
        url="http://example.com/stream",
    )
    media_info_reader.results["http://example.com/stream"] = playable(
        "http://example.com/stream"
    )

    target = fake_media_reader.find_playback_target(Uri("http://example.com/stream"))

    assert target is not None
    assert target.info == playable("http://example.com/stream")


def test_find_playback_target_gives_unverified_target_if_uri_cannot_be_read(
    fake_media_reader, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(url="http://example.com/stream", text="not a playlist")

    target = fake_media_reader.find_playback_target(Uri("http://example.com/stream"))

    assert target == PlaybackTarget(
        uri="http://example.com/stream", info=None, entry=None
    )


def test_find_playback_target_gives_none_if_uri_without_content_cannot_be_read(
    fake_media_reader,
):
    target = fake_media_reader.find_playback_target(Uri("rtsp://example.com/stream"))

    assert target is None


def test_find_playback_target_gives_none_if_nothing_is_found(
    fake_media_reader, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(url="http://example.com/radio.m3u", status_code=404)

    target = fake_media_reader.find_playback_target(Uri("http://example.com/radio.m3u"))

    assert target is None
