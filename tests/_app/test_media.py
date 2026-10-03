from collections.abc import Iterator

import httpx
import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from rich.console import Console

from mopidy._app import media
from mopidy._lib.paths import path_to_uri
from mopidy.config import Config
from mopidy.media import MediaInfo, MediaReadError, Reader
from mopidy.models import Album, Artist, Track
from mopidy.types import DurationMs
from tests import path_to_data_dir

CONFIG = Config({"proxy": {}})


class FakeMediaInfoReader:
    def __init__(self, results=None):
        self.results = results or {}

    def read_media_info(self, uri, *, timeout):
        result = self.results.get(uri, MediaReadError(f"Cannot read {uri}"))
        if isinstance(result, Exception):
            raise result
        return result


@pytest.fixture
def console() -> Console:
    return Console(record=True, width=80)


@pytest.fixture
def reader() -> Iterator[Reader]:
    with Reader.create(config=CONFIG, timeout=DurationMs(5000)) as reader:
        yield reader


@pytest.fixture
def media_info_reader() -> FakeMediaInfoReader:
    return FakeMediaInfoReader()


@pytest.fixture
def fake_reader(media_info_reader: FakeMediaInfoReader) -> Iterator[Reader]:
    with Reader(
        media_info_reader=media_info_reader,
        timeout=DurationMs(1000),
    ) as reader:
        yield reader


def playable(uri, **kwargs):
    return MediaInfo(track=Track(uri=uri, **kwargs), playable=True, seekable=False)


def test_info_of_audio_file(reader, console):
    path = path_to_data_dir("scanner/simple/song1.mp3")

    exit_code = media.info(reader, [str(path)], console)

    output = console.export_text()
    assert exit_code == 0
    assert output.splitlines()[0] == path_to_uri(path)
    assert "playable  yes" in output
    assert "4608 (0:04.608)" in output


def test_info_of_embedded_image(reader, console):
    path = path_to_data_dir("scanner/embedded-image.flac")

    exit_code = media.info(reader, [str(path)], console)

    assert exit_code == 0
    assert " bytes" in console.export_text()


def test_info_of_missing_file(reader, console, tmp_path):
    path = tmp_path / "missing.mp3"

    exit_code = media.info(reader, [str(path)], console)

    output = console.export_text()
    assert exit_code == 1
    assert output.splitlines()[0] == path_to_uri(path)
    assert "error" in output


def test_info_continues_after_an_error(reader, console, tmp_path):
    path = path_to_data_dir("scanner/simple/song1.mp3")

    exit_code = media.info(reader, [str(tmp_path / "missing.mp3"), str(path)], console)

    assert exit_code == 1
    assert "playable  yes" in console.export_text()


def test_info_of_file_path_and_file_uri_is_the_same(reader):
    path = path_to_data_dir("scanner/simple/song1.mp3")
    path_console = Console(record=True, width=80)
    uri_console = Console(record=True, width=80)

    media.info(reader, [str(path)], path_console)
    media.info(reader, [path_to_uri(path)], uri_console)

    assert path_console.export_text() == uri_console.export_text()


def test_info_shows_nested_models(fake_reader, media_info_reader, console):
    uri = "http://example.com/stream"
    media_info_reader.results[uri] = playable(
        uri,
        name="trackname",
        artists=frozenset([Artist(name="artistname")]),
        album=Album(name="albumname", num_tracks=2),
    )

    exit_code = media.info(fake_reader, [uri], console)

    output = console.export_text()
    assert exit_code == 0
    assert "uri   http://example.com/stream" in output
    assert "artists" in output
    assert "1\n" in output
    assert "name  artistname" in output
    assert "num_tracks  2" in output
    assert "seekable  no" in output


def test_info_does_not_truncate_the_root_uri(fake_reader, media_info_reader, console):
    uri = "http://example.com/" + "a" * 100
    media_info_reader.results[uri] = playable(uri, name="b" * 100)

    media.info(fake_reader, [uri], console)

    output = console.export_text()
    assert "a" * 100 in output.replace("\n", "")
    assert "b" * 100 not in output
    assert "…" in output


def test_playlist_entries(fake_reader, console, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="http://example.com/radio.xspf",
        text=(
            '<playlist version="1" xmlns="http://xspf.org/ns/0/"><trackList>'
            "<track>"
            "<title>Radio</title>"
            "<location>http://a.example.com/stream</location>"
            "<location>http://b.example.com/stream</location>"
            "</track>"
            "<track><location>http://c.example.com/stream</location></track>"
            "</trackList></playlist>"
        ),
    )

    exit_code = media.playlist_entries(
        fake_reader, ["http://example.com/radio.xspf"], console
    )

    output = console.export_text()
    assert exit_code == 0
    assert "entry 1" in output
    assert "name  Radio" in output
    assert "alternatives" in output
    assert "http://b.example.com/stream" in output
    assert "entry 2" in output


def test_playlist_entries_of_document_with_no_entries(
    fake_reader, console, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(url="http://example.com/radio.m3u", text="#EXTM3U\n")

    exit_code = media.playlist_entries(
        fake_reader, ["http://example.com/radio.m3u"], console
    )

    assert exit_code == 0
    assert "no playlist entries" in console.export_text()


def test_playlist_entries_of_failed_fetch(fake_reader, console, httpx_mock: HTTPXMock):
    httpx_mock.add_response(url="http://example.com/radio.m3u", status_code=404)

    exit_code = media.playlist_entries(
        fake_reader, ["http://example.com/radio.m3u"], console
    )

    assert exit_code == 1
    assert "error" in console.export_text()


def test_playback_target(
    fake_reader, media_info_reader, console, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        url="http://example.com/radio.pls",
        text="[playlist]\nFile1=http://b.example.com/stream\nTitle1=Radio\n",
        headers={"content-type": "audio/x-scpls"},
    )
    httpx_mock.add_response(
        url="http://b.example.com/stream",
        headers={"content-type": "audio/mpeg"},
    )
    media_info_reader.results["http://b.example.com/stream"] = playable(
        "http://b.example.com/stream"
    )

    exit_code = media.playback_target(
        fake_reader, ["http://example.com/radio.pls"], console
    )

    output = console.export_text()
    assert exit_code == 0
    assert "uri    http://b.example.com/stream" in output
    assert "info" in output
    assert "playable  yes" in output
    assert "entry" in output
    assert "name  Radio" in output


def test_playback_target_that_is_unverified(
    fake_reader, console, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        url="http://example.com/stream",
        headers={"content-type": "audio/mpeg"},
    )

    exit_code = media.playback_target(
        fake_reader, ["http://example.com/stream"], console
    )

    assert exit_code == 0
    assert "unverified" in console.export_text()


def test_playback_target_not_found(fake_reader, console, httpx_mock: HTTPXMock):
    httpx_mock.add_exception(httpx.ConnectError("Kaboom"))

    exit_code = media.playback_target(
        fake_reader, ["http://example.com/radio.pls"], console
    )

    assert exit_code == 1
    assert "no playback target found" in console.export_text()


def test_command_uses_the_proxy_config(
    mocker: MockerFixture, capsys, httpx_mock: HTTPXMock
):
    config = Config({"proxy": {"hostname": "proxy.example.com", "port": 8080}})
    mocker.patch.object(Config, "get_global", return_value=config)
    httpx_mock.add_response(
        url="http://example.com/radio.m3u",
        proxy_url="http://proxy.example.com:8080/",
        text="http://example.com/stream\n",
    )

    with pytest.raises(SystemExit) as exc_info:
        media.playlist_entries_command("http://example.com/radio.m3u")

    assert exc_info.value.code == 0
    assert "http://example.com/stream" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("arg", "uri"),
    [
        ("http://example.com/a.mp3", "http://example.com/a.mp3"),
        ("file:///tmp/a.mp3", "file:///tmp/a.mp3"),
        ("/tmp/missing/a.mp3", "file:///tmp/missing/a.mp3"),
    ],
)
def test_to_uri(arg, uri):
    assert media.to_uri(arg) == uri


def test_to_uri_of_existing_relative_path(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "http:a.mp3").touch()

    assert media.to_uri("http:a.mp3") == path_to_uri(tmp_path / "http:a.mp3")


def test_playlist_entries_shows_the_track_uri(
    fake_reader, console, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        url="http://example.com/radio.m3u", text="http://example.com/stream\n"
    )

    media.playlist_entries(fake_reader, ["http://example.com/radio.m3u"], console)

    assert "uri  http://example.com/stream" in console.export_text()


LONG_URI = "http://example.com/" + "a" * 100 + "/end"


def test_info_does_not_truncate_uris(fake_reader, media_info_reader, console):
    media_info_reader.results[LONG_URI] = playable(LONG_URI)

    media.info(fake_reader, [LONG_URI], console)

    output = console.export_text()
    assert output.count("/end") == 2
    assert "…" not in output


def test_info_does_not_truncate_errors(fake_reader, media_info_reader, console):
    media_info_reader.results[LONG_URI] = MediaReadError("x" * 100 + " the end")

    media.info(fake_reader, [LONG_URI], console)

    output = console.export_text()
    assert "the end" in output
    assert "…" not in output


def test_playlist_entries_does_not_truncate_uris(
    fake_reader, console, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(url="http://example.com/radio.m3u", text=f"{LONG_URI}\n")

    media.playlist_entries(fake_reader, ["http://example.com/radio.m3u"], console)

    output = console.export_text()
    assert output.count("/end") == 2
    assert "…" not in output


def test_playback_target_does_not_truncate_uris(
    fake_reader, media_info_reader, console
):
    media_info_reader.results[LONG_URI] = playable(LONG_URI)

    media.playback_target(fake_reader, [LONG_URI], console)

    output = console.export_text()
    assert output.count("/end") == 3
    assert "…" not in output
