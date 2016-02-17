from __future__ import absolute_import, unicode_literals

import mock

import pytest

from mopidy.internal import path
from mopidy.models import Track
from mopidy.stream import actor

from tests import path_to_data_dir


@pytest.fixture
def config():
    return {
        'proxy': {},
        'stream': {
            'timeout': 1000,
            'metadata_blacklist': [],
            'protocols': ['file'],
        },
        'file': {
            'enabled': False
        },
    }


@pytest.fixture
def audio():
    return mock.Mock()


@pytest.fixture
def track_uri():
    return path.path_to_uri(path_to_data_dir('song1.wav'))


def test_lookup_ignores_unknown_scheme(audio, config):
    backend = actor.StreamBackend(audio=audio, config=config)
    assert backend.library.lookup('http://example.com') == []


def test_lookup_respects_blacklist(audio, config, track_uri):
    config['stream']['metadata_blacklist'].append(track_uri)
    backend = actor.StreamBackend(audio=audio, config=config)

    assert backend.library.lookup(track_uri) == [Track(uri=track_uri)]


def test_lookup_respects_blacklist_globbing(audio, config, track_uri):
    blacklist_glob = path.path_to_uri(path_to_data_dir('')) + '*'
    config['stream']['metadata_blacklist'].append(blacklist_glob)
    backend = actor.StreamBackend(audio=audio, config=config)

    assert backend.library.lookup(track_uri) == [Track(uri=track_uri)]


def test_lookup_converts_uri_metadata_to_track(audio, config, track_uri):
    backend = actor.StreamBackend(audio=audio, config=config)

    result = backend.library.lookup(track_uri)
    assert result == [Track(length=4406, uri=track_uri)]
