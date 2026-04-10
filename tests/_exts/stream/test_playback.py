import logging
from pathlib import Path
from unittest import mock

import httpx
import pytest
from pytest_httpx import HTTPXMock

from mopidy import exceptions
from mopidy._exts.stream import actor
from mopidy.audio import scan

TIMEOUT = 1000
PLAYLIST_URI = "http://example.com/listen.m3u"
STREAM_URI = "http://example.com/stream.mp3"
BODY = """
#EXTM3U
http://example.com/stream.mp3
http://foo.bar/baz
""".strip()


@pytest.fixture
def config():
    return {
        "proxy": {},
        "stream": {
            "timeout": TIMEOUT,
            "metadata_blacklist": [],
            "protocols": ["http"],
        },
        "file": {"enabled": False},
    }


@pytest.fixture
def audio():
    return mock.Mock()


@pytest.fixture
def scanner():
    patcher = mock.patch.object(scan, "Scanner")
    yield patcher.start()()
    patcher.stop()


@pytest.fixture
def backend(audio, config, scanner):
    return actor.StreamBackend(audio=audio, config=config)


@pytest.fixture
def provider(backend):
    return backend.playback


class TestTranslateURI:
    def test_audio_stream_returns_same_uri(
        self, httpx_mock: HTTPXMock, scanner, provider
    ):
        scanner.scan.side_effect = [
            # Set playable to False to test detection by mimetype
            mock.Mock(mime="audio/mpeg", playable=False),
        ]

        result = provider.translate_uri(STREAM_URI)

        scanner.scan.assert_called_once_with(STREAM_URI, timeout=mock.ANY)
        assert result == STREAM_URI

    def test_playable_ogg_stream_is_not_considered_a_playlist(
        self, httpx_mock: HTTPXMock, scanner, provider
    ):
        scanner.scan.side_effect = [
            # Set playable to True to ignore detection as possible playlist
            mock.Mock(mime="application/ogg", playable=True),
        ]

        result = provider.translate_uri(STREAM_URI)

        scanner.scan.assert_called_once_with(STREAM_URI, timeout=mock.ANY)
        assert result == STREAM_URI

    def test_text_playlist_with_mpeg_stream(
        self, httpx_mock: HTTPXMock, scanner, provider, caplog
    ):
        caplog.set_level(logging.DEBUG)
        scanner.scan.side_effect = [
            # Scanning playlist
            mock.Mock(mime="text/foo", playable=False),
            # Scanning stream
            mock.Mock(mime="audio/mpeg", playable=True),
        ]
        httpx_mock.add_response(
            url=PLAYLIST_URI,
            status_code=200,
            text=BODY,
            headers={"content-type": "audio/x-mpegurl"},
        )

        result = provider.translate_uri(PLAYLIST_URI)

        assert scanner.scan.mock_calls == [
            mock.call(PLAYLIST_URI, timeout=mock.ANY),
            mock.call(STREAM_URI, timeout=mock.ANY),
        ]
        assert result == STREAM_URI

        # Check logging to ensure debuggability
        assert f"Unwrapping stream from URI: {PLAYLIST_URI}" in caplog.text
        assert f"Parsed playlist ({PLAYLIST_URI})" in caplog.text
        assert f"Unwrapping stream from URI: {STREAM_URI}" in caplog.text
        assert f"Unwrapped potential audio/mpeg stream: {STREAM_URI}" in caplog.text

        # Check proper HTTPX client setup
        request = httpx_mock.get_request()
        assert request is not None
        assert request.headers["User-Agent"].startswith("mopidy-stream/")

    def test_xml_playlist_with_mpeg_stream(
        self, httpx_mock: HTTPXMock, scanner, provider
    ):
        scanner.scan.side_effect = [
            # Scanning playlist
            mock.Mock(mime="application/xspf+xml", playable=False),
            # Scanning stream
            mock.Mock(mime="audio/mpeg", playable=True),
        ]
        httpx_mock.add_response(
            url=PLAYLIST_URI,
            status_code=200,
            text=BODY,
            headers={"content-type": "application/xspf+xml"},
        )

        result = provider.translate_uri(PLAYLIST_URI)

        assert scanner.scan.mock_calls == [
            mock.call(PLAYLIST_URI, timeout=mock.ANY),
            mock.call(STREAM_URI, timeout=mock.ANY),
        ]
        assert result == STREAM_URI

    def test_scan_fails_but_playlist_parsing_succeeds(
        self, httpx_mock: HTTPXMock, scanner, provider, caplog
    ):
        caplog.set_level(logging.DEBUG)
        scanner.scan.side_effect = [
            # Scanning playlist
            exceptions.ScannerError("some failure"),
            # Scanning stream
            mock.Mock(mime="audio/mpeg", playable=True),
        ]
        httpx_mock.add_response(
            url=PLAYLIST_URI,
            status_code=200,
            text=BODY,
            headers={"content-type": "audio/x-mpegurl"},
        )

        result = provider.translate_uri(PLAYLIST_URI)

        assert f"Unwrapping stream from URI: {PLAYLIST_URI}" in caplog.text
        assert f"GStreamer failed scanning URI ({PLAYLIST_URI})" in caplog.text
        assert f"Parsed playlist ({PLAYLIST_URI})" in caplog.text
        assert f"Unwrapped potential audio/mpeg stream: {STREAM_URI}" in caplog.text
        assert result == STREAM_URI

    def test_scan_fails_and_playlist_parsing_fails(
        self, httpx_mock: HTTPXMock, scanner, provider, caplog
    ):
        caplog.set_level(logging.DEBUG)
        scanner.scan.side_effect = exceptions.ScannerError("some failure")
        httpx_mock.add_response(
            url=STREAM_URI,
            status_code=200,
            content=b"some audio data",
            headers={"content-type": "audio/mpeg"},
        )

        result = provider.translate_uri(STREAM_URI)

        assert f"Unwrapping stream from URI: {STREAM_URI}" in caplog.text
        assert f"GStreamer failed scanning URI ({STREAM_URI})" in caplog.text
        assert (
            f"Failed parsing URI ({STREAM_URI}) as playlist; found potential stream."
            in caplog.text
        )
        assert result == STREAM_URI

    def test_failed_download_returns_none(
        self, httpx_mock: HTTPXMock, scanner, provider, caplog
    ):
        caplog.set_level(logging.DEBUG)
        scanner.scan.side_effect = [mock.Mock(mime="text/foo", playable=False)]

        httpx_mock.add_exception(httpx.HTTPError("Kaboom"), url=PLAYLIST_URI)

        result = provider.translate_uri(PLAYLIST_URI)

        assert result is None

        assert (
            f"Unwrapping stream from URI ({PLAYLIST_URI}) failed: error downloading URI"
        ) in caplog.text

    def test_playlist_references_itself(
        self, httpx_mock: HTTPXMock, scanner, provider, caplog
    ):
        caplog.set_level(logging.DEBUG)
        scanner.scan.side_effect = [mock.Mock(mime="text/foo", playable=False)]
        httpx_mock.add_response(
            url=PLAYLIST_URI,
            status_code=200,
            text=BODY.replace(STREAM_URI, PLAYLIST_URI),
            headers={"content-type": "audio/x-mpegurl"},
            is_reusable=True,
        )

        result = provider.translate_uri(PLAYLIST_URI)

        assert f"Unwrapping stream from URI: {PLAYLIST_URI}" in caplog.text
        assert (
            f"Parsed playlist ({PLAYLIST_URI}) and found new URI: {PLAYLIST_URI}"
        ) in caplog.text
        assert (
            f"Unwrapping stream from URI ({PLAYLIST_URI}) failed: "
            f"playlist referenced itself"
        ) in caplog.text
        assert result is None

    def test_playlist_with_relative_mpeg_stream(
        self, httpx_mock: HTTPXMock, scanner, provider, caplog
    ):
        caplog.set_level(logging.DEBUG)
        scanner.scan.side_effect = [
            # Scanning playlist
            mock.Mock(mime="text/foo", playable=False),
            # Scanning stream
            mock.Mock(mime="audio/mpeg", playable=True),
        ]
        httpx_mock.add_response(
            url=PLAYLIST_URI,
            status_code=200,
            text=BODY.replace(STREAM_URI, Path(STREAM_URI).name),
            headers={"content-type": "audio/x-mpegurl"},
        )

        result = provider.translate_uri(PLAYLIST_URI)

        assert scanner.scan.mock_calls == [
            mock.call(PLAYLIST_URI, timeout=mock.ANY),
            mock.call(STREAM_URI, timeout=mock.ANY),
        ]
        assert result == STREAM_URI

        assert (
            f"Parsed playlist ({PLAYLIST_URI}) and found new URI: "
            f"{Path(STREAM_URI).name}"
        ) in caplog.text
        assert f"Unwrapping stream from URI: {STREAM_URI}" in caplog.text
