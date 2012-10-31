import os

from mopidy import settings
from mopidy.backends.local import LocalBackend
from mopidy.models import Track
from mopidy.utils.path import path_to_uri

from tests import unittest, path_to_data_dir
from tests.backends.base.stored_playlists import (
    StoredPlaylistsControllerTest)
from tests.backends.local import generate_song


class LocalStoredPlaylistsControllerTest(
        StoredPlaylistsControllerTest, unittest.TestCase):

    backend_class = LocalBackend

    def test_created_playlist_is_persisted(self):
        path = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test.m3u')
        self.assert_(not os.path.exists(path))
        self.stored.create('test')
        self.assert_(os.path.exists(path))

    def test_saved_playlist_is_persisted(self):
        path1 = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test1.m3u')
        path2 = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test2.m3u')

        playlist = self.stored.create('test1')

        self.assertTrue(os.path.exists(path1))
        self.assertFalse(os.path.exists(path2))

        playlist = playlist.copy(name='test2')
        playlist = self.stored.save(playlist)

        self.assertFalse(os.path.exists(path1))
        self.assertTrue(os.path.exists(path2))

    def test_deleted_playlist_is_removed(self):
        path = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test.m3u')

        self.assertFalse(os.path.exists(path))

        playlist = self.stored.create('test')

        self.assertTrue(os.path.exists(path))

        self.stored.delete(playlist)

        self.assertFalse(os.path.exists(path))

    def test_playlist_contents_is_written_to_disk(self):
        track = Track(uri=generate_song(1))
        track_path = track.uri[len('file://'):]
        playlist = self.stored.create('test')
        playlist_path = playlist.uri[len('file://'):]
        playlist = playlist.copy(tracks=[track])
        playlist = self.stored.save(playlist)

        with open(playlist_path) as playlist_file:
            contents = playlist_file.read()

        self.assertEqual(track_path, contents.strip())

    def test_playlists_are_loaded_at_startup(self):
        playlist_path = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test.m3u')

        track = Track(uri=path_to_uri(path_to_data_dir('uri2')))
        playlist = self.stored.create('test')
        playlist = playlist.copy(tracks=[track])
        playlist = self.stored.save(playlist)

        backend = self.backend_class(audio=self.audio)

        self.assert_(backend.stored_playlists.playlists)
        self.assertEqual(
            path_to_uri(playlist_path),
            backend.stored_playlists.playlists[0].uri)
        self.assertEqual(
            playlist.name, backend.stored_playlists.playlists[0].name)
        self.assertEqual(
            track.uri, backend.stored_playlists.playlists[0].tracks[0].uri)

    @unittest.SkipTest
    def test_santitising_of_playlist_filenames(self):
        pass

    @unittest.SkipTest
    def test_playlist_folder_is_createad(self):
        pass
