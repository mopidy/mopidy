from unittest import mock

import pytest

from mopidy import backend
from tests import dummy_backend


def test_library_default_get_images_impl():
    library = dummy_backend.DummyLibraryProvider(backend=None)

    assert library.get_images(["trackuri"]) == {}


def test_library_lookup_many_falls_back():
    library = backend.LibraryProvider(backend=None)
    library.lookup = mock.Mock()

    library.lookup_many(uris=["dummy1:a", "dummy1:b"])

    library.lookup.assert_has_calls(
        [
            mock.call("dummy1:a"),
            mock.call("dummy1:b"),
        ],
    )


@pytest.fixture
def provider():
    return backend.PlaylistsProvider(backend=None)


def test_playlists_as_list_default_impl(provider):
    with pytest.raises(NotImplementedError):
        provider.as_list()


def test_playlists_get_items_default_impl(provider):
    with pytest.raises(NotImplementedError):
        provider.get_items("some uri")
