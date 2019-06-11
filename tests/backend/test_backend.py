from __future__ import absolute_import, unicode_literals

import unittest

from mopidy import backend

from tests import dummy_backend


class LibraryTest(unittest.TestCase):

    def test_default_get_images_impl(self):
        library = dummy_backend.DummyLibraryProvider(backend=None)

        self.assertEqual(library.get_images(['trackuri']), {})


class PlaylistsTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.provider = backend.PlaylistsProvider(backend=None)

    def test_as_list_default_impl(self):
        with self.assertRaises(NotImplementedError):
            self.provider.as_list()

    def test_get_items_default_impl(self):
        with self.assertRaises(NotImplementedError):
            self.provider.get_items('some uri')
