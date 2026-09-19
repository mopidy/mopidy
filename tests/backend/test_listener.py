from unittest import mock

import pytest

from mopidy import backend


@pytest.fixture
def listener():
    return backend.BackendListener()


def test_on_event_forwards_to_specific_handler(listener):
    listener.playlists_loaded = mock.Mock()

    listener.on_event("playlists_loaded")

    listener.playlists_loaded.assert_called_with()


def test_listener_has_default_impl_for_playlists_loaded(listener):
    listener.playlists_loaded()
