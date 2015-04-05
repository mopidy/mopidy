from __future__ import absolute_import, unicode_literals

import unittest

from mopidy import backend, models

from tests import dummy_backend


class LibraryTest(unittest.TestCase):

    def test_default_get_images_impl_falls_back_to_album_image(self):
        album = models.Album(images=['imageuri'])
        track = models.Track(uri='trackuri', album=album)

        library = dummy_backend.DummyLibraryProvider(backend=None)
        library.dummy_library.append(track)

        expected = {'trackuri': [models.Image(uri='imageuri')]}
        self.assertEqual(library.get_images(['trackuri']), expected)

    def test_default_get_images_impl_no_album_image(self):
        # default implementation now returns an empty list if no
        # images are found, though it's not required to
        track = models.Track(uri='trackuri')

        library = dummy_backend.DummyLibraryProvider(backend=None)
        library.dummy_library.append(track)

        expected = {'trackuri': []}
        self.assertEqual(library.get_images(['trackuri']), expected)


class PlaylistsTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.provider = backend.PlaylistsProvider(backend=None)

    def test_as_list_default_impl(self):
        with self.assertRaises(NotImplementedError):
            self.provider.as_list()

    def test_get_items_default_impl(self):
        with self.assertRaises(NotImplementedError):
            self.provider.get_items('some uri')
