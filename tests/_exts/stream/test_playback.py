from typing import Any
from unittest import mock

import pytest
from pytest_mock import MockerFixture

from mopidy._exts.stream import actor
from mopidy.media import MediaInfo, MediaReader, PlaybackTarget
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
def media_reader(mocker: MockerFixture) -> mock.Mock:
    media_reader = mock.Mock(spec=MediaReader)
    mocker.patch.object(MediaReader, "create", return_value=media_reader)
    return media_reader


@pytest.fixture
def provider(
    config: dict[str, Any], media_reader: mock.Mock
) -> actor.StreamPlaybackProvider:
    return actor.StreamBackend(audio=mock.Mock(), config=config).playback


def test_translate_uri_gives_the_playback_target(provider, media_reader):
    media_reader.find_playback_target.return_value = PlaybackTarget(
        uri=STREAM_URI,
        info=MediaInfo(track=Track(uri=STREAM_URI), playable=True, seekable=False),
        entry=None,
    )

    result = provider.translate_uri(PLAYLIST_URI)

    media_reader.find_playback_target.assert_called_once_with(PLAYLIST_URI)
    assert result == STREAM_URI


def test_translate_uri_gives_unverified_playback_target(provider, media_reader):
    media_reader.find_playback_target.return_value = PlaybackTarget(
        uri=STREAM_URI, info=None, entry=None
    )

    result = provider.translate_uri(PLAYLIST_URI)

    assert result == STREAM_URI


def test_translate_uri_gives_none_if_no_playback_target_is_found(
    provider, media_reader
):
    media_reader.find_playback_target.return_value = None

    result = provider.translate_uri(PLAYLIST_URI)

    assert result is None


def test_translate_uri_ignores_unknown_scheme(provider, media_reader):
    result = provider.translate_uri("rtsp://example.com/stream")

    assert result is None
    media_reader.find_playback_target.assert_not_called()


def target(*, seekable: bool, length: int | None = None) -> PlaybackTarget:
    return PlaybackTarget(
        uri=STREAM_URI,
        info=MediaInfo(
            track=Track(uri=STREAM_URI, length=length),
            playable=True,
            seekable=seekable,
        ),
        entry=None,
    )


def test_is_live_if_target_is_not_seekable_and_has_no_length(provider, media_reader):
    media_reader.find_playback_target.return_value = target(seekable=False)

    uri = provider.translate_uri(PLAYLIST_URI)

    assert provider.is_live(uri) is True


def test_is_not_live_if_target_is_seekable(provider, media_reader):
    media_reader.find_playback_target.return_value = target(seekable=True)

    uri = provider.translate_uri(PLAYLIST_URI)

    assert provider.is_live(uri) is False


def test_is_not_live_if_target_has_a_length(provider, media_reader):
    media_reader.find_playback_target.return_value = target(
        seekable=False, length=180_000
    )

    uri = provider.translate_uri(PLAYLIST_URI)

    assert provider.is_live(uri) is False


def test_is_not_live_if_target_is_not_playable(provider, media_reader):
    media_reader.find_playback_target.return_value = PlaybackTarget(
        uri=STREAM_URI,
        info=MediaInfo(track=Track(uri=STREAM_URI), playable=False, seekable=False),
        entry=None,
    )

    uri = provider.translate_uri(PLAYLIST_URI)

    assert provider.is_live(uri) is False


def test_is_not_live_if_target_is_unverified(provider, media_reader):
    media_reader.find_playback_target.return_value = PlaybackTarget(
        uri=STREAM_URI, info=None, entry=None
    )

    uri = provider.translate_uri(PLAYLIST_URI)

    assert provider.is_live(uri) is False


def test_is_not_live_if_uri_matches_metadata_blacklist(config, media_reader):
    config["stream"]["metadata_blacklist"] = [STREAM_URI]
    provider = actor.StreamBackend(audio=mock.Mock(), config=config).playback

    uri = provider.translate_uri(STREAM_URI)

    assert provider.is_live(uri) is False
    media_reader.find_playback_target.assert_not_called()


def test_is_not_live_for_another_uri(provider, media_reader):
    media_reader.find_playback_target.return_value = target(seekable=False)

    provider.translate_uri(PLAYLIST_URI)

    assert provider.is_live("http://example.com/other.mp3") is False


def test_is_not_live_after_translating_another_uri(provider, media_reader):
    media_reader.find_playback_target.return_value = target(seekable=False)
    uri = provider.translate_uri(PLAYLIST_URI)
    media_reader.find_playback_target.return_value = None

    provider.translate_uri("http://example.com/gone.m3u")

    assert provider.is_live(uri) is False


def test_is_not_live_before_translate_uri(provider):
    assert provider.is_live(STREAM_URI) is False
