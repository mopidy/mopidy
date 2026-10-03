from typing import Any
from unittest import mock

import pytest
from pytest_mock import MockerFixture

from mopidy._exts.stream import actor
from mopidy.media import MediaInfo, PlaybackTarget, Reader
from mopidy.models import Track

PLAYLIST_URI = "http://example.com/listen.m3u"
STREAM_URI = "http://example.com/stream.mp3"


@pytest.fixture
def config():
    return {
        "proxy": {},
        "stream": {
            "timeout": 1000,
            "metadata_blacklist": [],
            "protocols": ["http"],
        },
        "file": {"enabled": False},
    }


@pytest.fixture
def reader(mocker: MockerFixture) -> mock.Mock:
    reader = mock.Mock(spec=Reader)
    mocker.patch.object(Reader, "create", return_value=reader)
    return reader


@pytest.fixture
def provider(config: dict[str, Any], reader: mock.Mock) -> actor.StreamPlaybackProvider:
    return actor.StreamBackend(audio=mock.Mock(), config=config).playback


def test_translate_uri_gives_the_playback_target(provider, reader):
    reader.find_playback_target.return_value = PlaybackTarget(
        uri=STREAM_URI,
        info=MediaInfo(track=Track(uri=STREAM_URI), playable=True, seekable=False),
        entry=None,
    )

    result = provider.translate_uri(PLAYLIST_URI)

    reader.find_playback_target.assert_called_once_with(PLAYLIST_URI)
    assert result == STREAM_URI


def test_translate_uri_gives_unverified_playback_target(provider, reader):
    reader.find_playback_target.return_value = PlaybackTarget(
        uri=STREAM_URI, info=None, entry=None
    )

    result = provider.translate_uri(PLAYLIST_URI)

    assert result == STREAM_URI


def test_translate_uri_gives_none_if_no_playback_target_is_found(provider, reader):
    reader.find_playback_target.return_value = None

    result = provider.translate_uri(PLAYLIST_URI)

    assert result is None


def test_translate_uri_ignores_unknown_scheme(provider, reader):
    result = provider.translate_uri("rtsp://example.com/stream")

    assert result is None
    reader.find_playback_target.assert_not_called()
