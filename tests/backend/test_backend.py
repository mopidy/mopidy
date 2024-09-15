import unittest
from unittest import mock

import pytest

from mopidy import backend
from tests import dummy_backend


class LibraryTest(unittest.TestCase):
    def test_default_get_images_impl(self):
        library = dummy_backend.DummyLibraryProvider(backend=None)

        assert library.get_images(["trackuri"]) == {}

    def test_lookup_many_falls_back(self):
        library = backend.LibraryProvider(backend=None)
        library.lookup = mock.Mock()

        library.lookup_many(uris=["dummy1:a", "dummy1:b"])

        library.lookup.assert_has_calls(
            [
                mock.call("dummy1:a"),
                mock.call("dummy1:b"),
            ],
        )


class PlaylistsTest(unittest.TestCase):
    def setUp(self):
        self.provider = backend.PlaylistsProvider(backend=None)

    def test_as_list_default_impl(self):
        with pytest.raises(NotImplementedError):
            self.provider.as_list()

    def test_get_items_default_impl(self):
        with pytest.raises(NotImplementedError):
            self.provider.get_items("some uri")
