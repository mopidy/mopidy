from __future__ import absolute_import, unicode_literals

import unittest

import mock

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
    def test_playlists_default_impl(self):
        provider = backend.PlaylistsProvider(backend=None)

        self.assertEqual(provider.playlists, [])

        with self.assertRaises(NotImplementedError):
            provider.playlists = []

    def test_get_playlists_impl_falls_back_to_playlists_property(self):
        provider = backend.PlaylistsProvider(backend=None)

        with mock.patch(
                'mopidy.backend.PlaylistsProvider.playlists',
                new_callable=mock.PropertyMock) as mock_playlists_prop:
            mock_playlists_prop.return_value = mock.sentinel.playlists_prop

            result = provider.get_playlists()

        self.assertEqual(result, mock.sentinel.playlists_prop)
