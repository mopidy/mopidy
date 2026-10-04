import re

import httpx
import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from rich.console import Console

from mopidy._app import media
from mopidy._lib.paths import path_to_uri
from mopidy.config import Config
from mopidy.media import MediaInfo, MediaReader, MediaReadError
from mopidy.models import Track
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


@pytest.fixture(autouse=True)
def config(mocker: MockerFixture) -> None:
    mocker.patch.object(Config, "get_global", return_value=CONFIG)


@pytest.fixture
def console(mocker: MockerFixture) -> Console:
    console = Console(record=True, width=80)
    mocker.patch.object(media, "Console", return_value=console)
    return console


@pytest.fixture
def media_info_reader() -> FakeMediaInfoReader:
    return FakeMediaInfoReader()


@pytest.fixture
def fake_media_reader(
    media_info_reader: FakeMediaInfoReader, mocker: MockerFixture
) -> MediaReader:
    media_reader = MediaReader(
        media_info_reader=media_info_reader,
        timeout=DurationMs(1000),
    )
    mocker.patch.object(MediaReader, "create", return_value=media_reader)
    return media_reader


def run(command, *targets: str) -> int:
    with pytest.raises(SystemExit) as exc_info:
        command(*targets)
    return exc_info.value.code


def playable(uri, **kwargs):
    return MediaInfo(track=Track(uri=uri, **kwargs), playable=True, seekable=False)


def test_info_of_audio_file(console):
    path = path_to_data_dir("scanner/simple/song1.mp3")

    exit_code = run(media.info, str(path))

    output = console.export_text()
    assert exit_code == 0
    assert output.replace("\n", "").startswith(path_to_uri(path))
    assert "playable  yes" in output
    assert "4608 (0:04.608)" in output


def test_info_of_embedded_image(console):
    path = path_to_data_dir("scanner/embedded-image.flac")

    exit_code = run(media.info, str(path))

    assert exit_code == 0
    assert re.search(r"data  \d+ bytes", console.export_text())


def test_info_of_missing_file(console, tmp_path):
    path = tmp_path / "missing.mp3"

    exit_code = run(media.info, str(path))

    output = console.export_text()
    assert exit_code == 1
    assert output.replace("\n", "").startswith(path_to_uri(path))
    assert "error" in output


def test_info_continues_after_an_error(console, tmp_path):
    path = path_to_data_dir("scanner/simple/song1.mp3")

    exit_code = run(media.info, str(tmp_path / "missing.mp3"), str(path))

    assert exit_code == 1
    assert "playable  yes" in console.export_text()


def test_info_of_file_path_and_file_uri_is_the_same(mocker: MockerFixture):
    path = path_to_data_dir("scanner/simple/song1.mp3")
    path_console = Console(record=True, width=80)
    uri_console = Console(record=True, width=80)
    mocker.patch.object(media, "Console", side_effect=[path_console, uri_console])

    run(media.info, str(path))
    run(media.info, path_to_uri(path))

    assert path_console.export_text() == uri_console.export_text()


def test_info_does_not_truncate_the_root_uri(
    fake_media_reader, media_info_reader, console
):
    uri = "http://example.com/" + "a" * 100
    media_info_reader.results[uri] = playable(uri)

    run(media.info, uri)

    output = console.export_text()
    assert output.replace("\n", "").startswith(uri)


def test_playlist_entries(fake_media_reader, console, httpx_mock: HTTPXMock):
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

    exit_code = run(media.playlist_entries, "http://example.com/radio.xspf")

    output = console.export_text()
    assert exit_code == 0
    assert "├── 1\n" in output
    assert "name   Radio" in output
    assert "alternatives" in output
    assert "2  http://b.example.com/stream" in output
    assert "└── 2\n" in output


def test_playlist_entries_of_document_with_no_entries(
    fake_media_reader, console, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(url="http://example.com/radio.m3u", text="#EXTM3U\n")

    exit_code = run(media.playlist_entries, "http://example.com/radio.m3u")

    assert exit_code == 0
    assert "no playlist entries" in console.export_text()


def test_playlist_entries_of_failed_fetch(
    fake_media_reader, console, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(url="http://example.com/radio.m3u", status_code=404)

    exit_code = run(media.playlist_entries, "http://example.com/radio.m3u")

    assert exit_code == 1
    assert "error" in console.export_text()


def test_playback_target(
    fake_media_reader, media_info_reader, console, httpx_mock: HTTPXMock
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

    exit_code = run(media.playback_target, "http://example.com/radio.pls")

    output = console.export_text()
    assert exit_code == 0
    assert "uri  http://b.example.com/stream" in output
    assert "info" in output
    assert "playable  yes" in output
    assert "entry" in output
    assert "name   Radio" in output


def test_playback_target_that_is_unverified(
    fake_media_reader, console, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        url="http://example.com/stream",
        headers={"content-type": "audio/mpeg"},
    )

    exit_code = run(media.playback_target, "http://example.com/stream")

    output = console.export_text()
    assert exit_code == 0
    assert "info   none" in output
    assert "entry  none" in output


def test_playback_target_not_found(fake_media_reader, console, httpx_mock: HTTPXMock):
    httpx_mock.add_exception(httpx.ConnectError("Kaboom"))

    exit_code = run(media.playback_target, "http://example.com/radio.pls")

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

    exit_code = run(media.playlist_entries, "http://example.com/radio.m3u")

    assert exit_code == 0
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


LONG_URI = "http://example.com/" + "a" * 100 + "/end"


def test_info_does_not_truncate_errors(fake_media_reader, media_info_reader, console):
    media_info_reader.results[LONG_URI] = MediaReadError("x" * 100 + " the end")

    run(media.info, LONG_URI)

    output = console.export_text()
    assert "the end" in output
    assert "…" not in output
