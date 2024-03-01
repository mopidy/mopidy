import unittest

import pytest
from mopidy import backend

from tests import dummy_backend


class LibraryTest(unittest.TestCase):
    def test_default_get_images_impl(self):
        library = dummy_backend.DummyLibraryProvider(backend=None)

        assert library.get_images(["trackuri"]) == {}


class PlaylistsTest(unittest.TestCase):
    def setUp(self):
        self.provider = backend.PlaylistsProvider(backend=None)

    def test_as_list_default_impl(self):
        with pytest.raises(NotImplementedError):
            self.provider.as_list()

    def test_get_items_default_impl(self):
        with pytest.raises(NotImplementedError):
            self.provider.get_items("some uri")
