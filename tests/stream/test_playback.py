from __future__ import absolute_import, unicode_literals

import mock

import pytest

import requests

import responses

from mopidy import exceptions
from mopidy.audio import scan
from mopidy.stream import actor


TIMEOUT = 1000
URI = 'http://example.com/listen.m3u'
BODY = """
#EXTM3U
http://example.com/stream.mp3
http://foo.bar/baz
""".strip()


@pytest.fixture
def config():
    return {
        'proxy': {},
        'stream': {
            'timeout': TIMEOUT,
        },
    }


@pytest.fixture
def audio():
    return mock.Mock()


@pytest.fixture
def scanner():
    scanner = mock.Mock(spec=scan.Scanner)
    scanner.scan.return_value.mime = 'text/foo'
    return scanner


@pytest.fixture
def backend(scanner):
    backend = mock.Mock()
    backend.uri_schemes = ['file']
    backend._scanner = scanner
    return backend


@pytest.fixture
def provider(audio, backend, config):
    return actor.StreamPlaybackProvider(audio, backend, config)


@responses.activate
def test_translate_uri_of_audio_stream_returns_same_uri(
        scanner, provider):

    scanner.scan.return_value.mime = 'audio/ogg'

    result = provider.translate_uri(URI)

    scanner.scan.assert_called_once_with(URI)
    assert result == URI


@responses.activate
def test_translate_uri_of_playlist_returns_first_uri_in_list(
        scanner, provider):

    responses.add(
        responses.GET, URI, body=BODY, content_type='audio/x-mpegurl')

    result = provider.translate_uri(URI)

    scanner.scan.assert_called_once_with(URI)
    assert result == 'http://example.com/stream.mp3'
    assert responses.calls[0].request.headers['User-Agent'].startswith(
        'Mopidy-Stream/')


@responses.activate
def test_translate_uri_of_playlist_with_xml_mimetype(scanner, provider):
    scanner.scan.return_value.mime = 'application/xspf+xml'
    responses.add(
        responses.GET, URI, body=BODY, content_type='application/xspf+xml')

    result = provider.translate_uri(URI)

    scanner.scan.assert_called_once_with(URI)
    assert result == 'http://example.com/stream.mp3'


def test_translate_uri_when_scanner_fails(scanner, provider, caplog):
    scanner.scan.side_effect = exceptions.ScannerError('foo failed')

    result = provider.translate_uri('bar')

    assert result is None
    assert 'Problem scanning URI bar: foo failed' in caplog.text()


@responses.activate
def test_translate_uri_when_playlist_download_fails(provider, caplog):
    responses.add(responses.GET, URI, body=BODY, status=500)

    result = provider.translate_uri(URI)

    assert result is None
    assert 'Problem downloading stream playlist' in caplog.text()


def test_translate_uri_times_out_if_connection_times_out(provider, caplog):
    with mock.patch.object(actor.requests, 'Session') as session_mock:
        get_mock = session_mock.return_value.get
        get_mock.side_effect = requests.exceptions.Timeout

        result = provider.translate_uri(URI)

    get_mock.assert_called_once_with(URI, timeout=1.0, stream=True)
    assert result is None
    assert (
        'Download of stream playlist (%s) failed due to connection '
        'timeout after 1.000s' % URI in caplog.text())


@responses.activate
def test_translate_uri_times_out_if_download_is_slow(provider, caplog):
    responses.add(
        responses.GET, URI, body=BODY, content_type='audio/x-mpegurl')

    with mock.patch.object(actor, 'time') as time_mock:
        time_mock.time.side_effect = [0, TIMEOUT + 1]

        result = provider.translate_uri(URI)

    assert result is None
    assert (
        'Download of stream playlist (%s) failed due to download taking '
        'more than 1.000s' % URI in caplog.text())
