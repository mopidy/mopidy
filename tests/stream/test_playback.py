from __future__ import absolute_import, unicode_literals

import mock

import pytest

import requests.exceptions

import responses

from mopidy import exceptions
from mopidy.audio import scan
from mopidy.stream import actor


TIMEOUT = 1000
PLAYLIST_URI = 'http://example.com/listen.m3u'
STREAM_URI = 'http://example.com/stream.mp3'
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
            'metadata_blacklist': [],
            'protocols': ['http'],
        },
        'file': {
            'enabled': False
        },
    }


@pytest.fixture
def audio():
    return mock.Mock()


@pytest.yield_fixture
def scanner():
    patcher = mock.patch.object(scan, 'Scanner')
    yield patcher.start()()
    patcher.stop()


@pytest.fixture
def backend(audio, config, scanner):
    return actor.StreamBackend(audio=audio, config=config)


@pytest.fixture
def provider(backend):
    return backend.playback


class TestTranslateURI(object):

    @responses.activate
    def test_audio_stream_returns_same_uri(self, scanner, provider):
        scanner.scan.side_effect = [
            # Set playable to False to test detection by mimetype
            mock.Mock(mime='audio/mpeg', playable=False),
        ]

        result = provider.translate_uri(STREAM_URI)

        scanner.scan.assert_called_once_with(STREAM_URI, timeout=mock.ANY)
        assert result == STREAM_URI

    @responses.activate
    def test_playable_ogg_stream_is_not_considered_a_playlist(
            self, scanner, provider):

        scanner.scan.side_effect = [
            # Set playable to True to ignore detection as possible playlist
            mock.Mock(mime='application/ogg', playable=True),
        ]

        result = provider.translate_uri(STREAM_URI)

        scanner.scan.assert_called_once_with(STREAM_URI, timeout=mock.ANY)
        assert result == STREAM_URI

    @responses.activate
    def test_text_playlist_with_mpeg_stream(
            self, scanner, provider, caplog):

        scanner.scan.side_effect = [
            # Scanning playlist
            mock.Mock(mime='text/foo', playable=False),
            # Scanning stream
            mock.Mock(mime='audio/mpeg', playable=True),
        ]
        responses.add(
            responses.GET, PLAYLIST_URI,
            body=BODY, content_type='audio/x-mpegurl')

        result = provider.translate_uri(PLAYLIST_URI)

        assert scanner.scan.mock_calls == [
            mock.call(PLAYLIST_URI, timeout=mock.ANY),
            mock.call(STREAM_URI, timeout=mock.ANY),
        ]
        assert result == STREAM_URI

        # Check logging to ensure debuggability
        assert 'Unwrapping stream from URI: %s' % PLAYLIST_URI
        assert 'Parsed playlist (%s)' % PLAYLIST_URI in caplog.text()
        assert 'Unwrapping stream from URI: %s' % STREAM_URI
        assert (
            'Unwrapped potential audio/mpeg stream: %s' % STREAM_URI
            in caplog.text())

        # Check proper Requests session setup
        assert responses.calls[0].request.headers['User-Agent'].startswith(
            'Mopidy-Stream/')

    @responses.activate
    def test_xml_playlist_with_mpeg_stream(self, scanner, provider):
        scanner.scan.side_effect = [
            # Scanning playlist
            mock.Mock(mime='application/xspf+xml', playable=False),
            # Scanning stream
            mock.Mock(mime='audio/mpeg', playable=True),
        ]
        responses.add(
            responses.GET, PLAYLIST_URI,
            body=BODY, content_type='application/xspf+xml')

        result = provider.translate_uri(PLAYLIST_URI)

        assert scanner.scan.mock_calls == [
            mock.call(PLAYLIST_URI, timeout=mock.ANY),
            mock.call(STREAM_URI, timeout=mock.ANY),
        ]
        assert result == STREAM_URI

    @responses.activate
    def test_scan_fails_but_playlist_parsing_succeeds(
            self, scanner, provider, caplog):

        scanner.scan.side_effect = [
            # Scanning playlist
            exceptions.ScannerError('some failure'),
            # Scanning stream
            mock.Mock(mime='audio/mpeg', playable=True),
        ]
        responses.add(
            responses.GET, PLAYLIST_URI,
            body=BODY, content_type='audio/x-mpegurl')

        result = provider.translate_uri(PLAYLIST_URI)

        assert 'Unwrapping stream from URI: %s' % PLAYLIST_URI
        assert (
            'GStreamer failed scanning URI (%s)' % PLAYLIST_URI
            in caplog.text())
        assert 'Parsed playlist (%s)' % PLAYLIST_URI in caplog.text()
        assert (
            'Unwrapped potential audio/mpeg stream: %s' % STREAM_URI
            in caplog.text())
        assert result == STREAM_URI

    @responses.activate
    def test_scan_fails_and_playlist_parsing_fails(
            self, scanner, provider, caplog):

        scanner.scan.side_effect = exceptions.ScannerError('some failure')
        responses.add(
            responses.GET, STREAM_URI,
            body=b'some audio data', content_type='audio/mpeg')

        result = provider.translate_uri(STREAM_URI)

        assert 'Unwrapping stream from URI: %s' % STREAM_URI
        assert (
            'GStreamer failed scanning URI (%s)' % STREAM_URI
            in caplog.text())
        assert (
            'Failed parsing URI (%s) as playlist; found potential stream.'
            % STREAM_URI in caplog.text())
        assert result == STREAM_URI

    @responses.activate
    def test_failed_download_returns_none(self, scanner, provider, caplog):
        scanner.scan.side_effect = [
            mock.Mock(mime='text/foo', playable=False)
        ]

        responses.add(
            responses.GET, PLAYLIST_URI,
            body=requests.exceptions.HTTPError('Kaboom'))

        result = provider.translate_uri(PLAYLIST_URI)

        assert result is None

        assert (
            'Unwrapping stream from URI (%s) failed: '
            'error downloading URI' % PLAYLIST_URI) in caplog.text()

    @responses.activate
    def test_playlist_references_itself(self, scanner, provider, caplog):
        scanner.scan.side_effect = [
            mock.Mock(mime='text/foo', playable=False)
        ]
        responses.add(
            responses.GET, PLAYLIST_URI,
            body=BODY.replace(STREAM_URI, PLAYLIST_URI),
            content_type='audio/x-mpegurl')

        result = provider.translate_uri(PLAYLIST_URI)

        assert 'Unwrapping stream from URI: %s' % PLAYLIST_URI in caplog.text()
        assert (
            'Parsed playlist (%s) and found new URI: %s'
            % (PLAYLIST_URI, PLAYLIST_URI)) in caplog.text()
        assert (
            'Unwrapping stream from URI (%s) failed: '
            'playlist referenced itself' % PLAYLIST_URI) in caplog.text()
        assert result is None
