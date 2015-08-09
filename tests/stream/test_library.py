from __future__ import absolute_import, unicode_literals

import mock

import pytest

from mopidy.audio import scan
from mopidy.internal import path
from mopidy.models import Track
from mopidy.stream import actor

from tests import path_to_data_dir


@pytest.fixture
def scanner():
    return scan.Scanner(timeout=100, proxy_config={})


@pytest.fixture
def backend(scanner):
    backend = mock.Mock()
    backend.uri_schemes = ['file']
    backend._scanner = scanner
    return backend


@pytest.fixture
def track_uri():
    return path.path_to_uri(path_to_data_dir('song1.wav'))


def test_lookup_ignores_unknown_scheme(backend):
    library = actor.StreamLibraryProvider(backend, [])

    assert library.lookup('http://example.com') == []


def test_lookup_respects_blacklist(backend, track_uri):
    library = actor.StreamLibraryProvider(backend, [track_uri])

    assert library.lookup(track_uri) == [Track(uri=track_uri)]


def test_lookup_respects_blacklist_globbing(backend, track_uri):
    blacklist = [path.path_to_uri(path_to_data_dir('')) + '*']
    library = actor.StreamLibraryProvider(backend, blacklist)

    assert library.lookup(track_uri) == [Track(uri=track_uri)]


def test_lookup_converts_uri_metadata_to_track(backend, track_uri):
    library = actor.StreamLibraryProvider(backend, [])

    assert library.lookup(track_uri) == [Track(length=4406, uri=track_uri)]
