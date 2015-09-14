from __future__ import absolute_import, unicode_literals

import mock

import pytest

import requests

import responses

from mopidy.internal import http


TIMEOUT = 1000
URI = 'http://example.com/foo.txt'
BODY = "This is the contents of foo.txt."


@pytest.fixture
def session():
    return requests.Session()


@pytest.fixture
def session_mock():
    return mock.Mock(spec=requests.Session)


@responses.activate
def test_download_on_server_side_error(session, caplog):
    responses.add(responses.GET, URI, body=BODY, status=500)

    result = http.download(session, URI)

    assert result is None
    assert 'Problem downloading' in caplog.text()


def test_download_times_out_if_connection_times_out(session_mock, caplog):
    session_mock.get.side_effect = requests.exceptions.Timeout

    result = http.download(session_mock, URI, timeout=1.0)

    session_mock.get.assert_called_once_with(URI, timeout=1.0, stream=True)
    assert result is None
    assert (
        'Download of %r failed due to connection timeout after 1.000s' % URI
        in caplog.text())


@responses.activate
def test_download_times_out_if_download_is_slow(session, caplog):
    responses.add(responses.GET, URI, body=BODY, content_type='text/plain')

    with mock.patch.object(http, 'time') as time_mock:
        time_mock.time.side_effect = [0, TIMEOUT + 1]

        result = http.download(session, URI)

    assert result is None
    assert (
        'Download of %r failed due to download taking more than 1.000s' % URI
        in caplog.text())
