from unittest import mock

import httpx
import pytest
from pytest_httpx import HTTPXMock

from mopidy._exts.stream import http

TIMEOUT = 1000
URI = "http://example.com/foo.txt"
BODY = "This is the contents of foo.txt."


@pytest.fixture
def client():
    client = httpx.Client()
    yield client
    client.close()


def test_download_on_server_side_error(httpx_mock: HTTPXMock, client, caplog):
    httpx_mock.add_response(url=URI, status_code=500, text=BODY)

    result = http.download(client, URI)

    assert result is None
    assert "Problem downloading" in caplog.text


def test_download_times_out_if_connection_times_out(
    httpx_mock: HTTPXMock, client, caplog
):
    httpx_mock.add_exception(httpx.TimeoutException("timed out"), url=URI)

    result = http.download(client, URI, timeout=1.0)

    assert result is None
    assert (
        f"Download of {URI!r} failed due to connection timeout after 1.000s"
        in caplog.text
    )


def test_download_times_out_if_download_is_slow(httpx_mock: HTTPXMock, client, caplog):
    httpx_mock.add_response(url=URI, status_code=200, text=BODY)

    with mock.patch.object(http, "time") as time_mock:
        time_mock.time.side_effect = [0, TIMEOUT + 1]

        result = http.download(client, URI)

    assert result is None
    assert (
        f"Download of {URI!r} failed due to download taking more than 1.000s"
        in caplog.text
    )
