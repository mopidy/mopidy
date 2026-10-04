from typing import Any
from unittest import mock

import pytest
from pytest_mock import MockerFixture

from mopidy._exts.stream import actor
from mopidy._lib import paths
from mopidy.media import MediaInfo, MediaReader, PlaybackTarget
from mopidy.models import Track
from tests import path_to_data_dir


@pytest.fixture
def config():
    return {
        "proxy": {},
        "stream": {
            "timeout": 1000,
            "metadata_blacklist": [],
            "protocols": ["file"],
        },
        "file": {"enabled": False},
    }


@pytest.fixture
def audio():
    return mock.Mock()


@pytest.fixture
def track_uri():
    return paths.path_to_uri(path_to_data_dir("song1.wav"))


def test_lookup_ignores_unknown_scheme(audio, config):
    backend = actor.StreamBackend(audio=audio, config=config)
    assert backend.library.lookup("http://example.com") == []


def test_lookup_respects_blacklist(audio, config, track_uri):
    config["stream"]["metadata_blacklist"].append(track_uri)
    backend = actor.StreamBackend(audio=audio, config=config)

    assert backend.library.lookup(track_uri) == [Track(uri=track_uri)]


def test_lookup_respects_blacklist_globbing(audio, config, track_uri):
    blacklist_glob = paths.path_to_uri(path_to_data_dir("")) + "*"
    config["stream"]["metadata_blacklist"].append(blacklist_glob)
    backend = actor.StreamBackend(audio=audio, config=config)

    assert backend.library.lookup(track_uri) == [Track(uri=track_uri)]


def test_lookup_converts_uri_metadata_to_track(audio, config, track_uri):
    backend = actor.StreamBackend(audio=audio, config=config)

    result = backend.library.lookup(track_uri)

    assert len(result) == 1
    track = result[0]
    assert track.uri == track_uri
    assert track.length == 4406


@pytest.fixture
def media_reader(config: dict[str, Any], mocker: MockerFixture) -> mock.Mock:
    config["stream"]["protocols"] = ["http"]
    media_reader = mock.Mock(spec=MediaReader)
    mocker.patch.object(MediaReader, "create", return_value=media_reader)
    return media_reader


def test_lookup_gives_metadata_of_playback_target_under_original_uri(
    audio, config, media_reader
):
    media_reader.find_playback_target.return_value = PlaybackTarget(
        uri="http://example.com/stream.mp3",
        info=MediaInfo(
            track=Track(uri="http://example.com/stream.mp3", name="a stream"),
            playable=True,
            seekable=False,
        ),
        entry=None,
    )
    backend = actor.StreamBackend(audio=audio, config=config)

    result = backend.library.lookup("http://example.com/listen.m3u")

    media_reader.find_playback_target.assert_called_once_with(
        "http://example.com/listen.m3u"
    )
    assert result == [Track(uri="http://example.com/listen.m3u", name="a stream")]


def test_lookup_of_unverified_playback_target_gives_track_with_only_uri(
    audio, config, media_reader
):
    media_reader.find_playback_target.return_value = PlaybackTarget(
        uri="http://example.com/stream.mp3", info=None, entry=None
    )
    backend = actor.StreamBackend(audio=audio, config=config)

    result = backend.library.lookup("http://example.com/listen.m3u")

    assert result == [Track(uri="http://example.com/listen.m3u")]


def test_lookup_with_no_playback_target_gives_track_with_only_uri(
    audio, config, media_reader
):
    media_reader.find_playback_target.return_value = None
    backend = actor.StreamBackend(audio=audio, config=config)

    result = backend.library.lookup("http://example.com/listen.m3u")

    assert result == [Track(uri="http://example.com/listen.m3u")]
