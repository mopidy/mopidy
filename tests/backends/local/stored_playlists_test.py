import os
import sys

from mopidy import settings
from mopidy.backends.local import LocalBackend
from mopidy.models import Playlist, Track
from mopidy.utils.path import path_to_uri

from tests import unittest, path_to_data_dir
from tests.backends.base.stored_playlists import (
    StoredPlaylistsControllerTest)
from tests.backends.local import generate_song


@unittest.skipIf(sys.platform == 'win32',
    'Our Windows build server does not support GStreamer yet')
class LocalStoredPlaylistsControllerTest(StoredPlaylistsControllerTest,
        unittest.TestCase):

    backend_class = LocalBackend

    def test_created_playlist_is_persisted(self):
        path = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test.m3u')
        self.assert_(not os.path.exists(path))
        self.stored.create('test')
        self.assert_(os.path.exists(path))

    def test_saved_playlist_is_persisted(self):
        path = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test2.m3u')
        self.assert_(not os.path.exists(path))
        self.stored.save(Playlist(name='test2'))
        self.assert_(os.path.exists(path))

    def test_deleted_playlist_get_removed(self):
        playlist = self.stored.create('test')
        self.stored.delete(playlist)
        path = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test.m3u')
        self.assert_(not os.path.exists(path))

    def test_renamed_playlist_gets_moved(self):
        playlist = self.stored.create('test')
        file1 = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test.m3u')
        file2 = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test2.m3u')
        self.assert_(not os.path.exists(file2))
        self.stored.rename(playlist, 'test2')
        self.assert_(not os.path.exists(file1))
        self.assert_(os.path.exists(file2))

    def test_playlist_contents_get_written_to_disk(self):
        track = Track(uri=generate_song(1))
        uri = track.uri[len('file://'):]
        playlist = Playlist(tracks=[track], name='test')
        path = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test.m3u')

        self.stored.save(playlist)

        with open(path) as playlist_file:
            contents = playlist_file.read()

        self.assertEqual(uri, contents.strip())

    def test_playlists_are_loaded_at_startup(self):
        track = Track(uri=path_to_uri(path_to_data_dir('uri2')))
        playlist = Playlist(tracks=[track], name='test')

        self.stored.save(playlist)

        self.backend = self.backend_class()
        self.stored = self.backend.stored_playlists

        self.assert_(self.stored.playlists)
        self.assertEqual('test', self.stored.playlists[0].name)
        self.assertEqual(track.uri, self.stored.playlists[0].tracks[0].uri)

    @unittest.SkipTest
    def test_santitising_of_playlist_filenames(self):
        pass

    @unittest.SkipTest
    def test_playlist_folder_is_createad(self):
        pass

    @unittest.SkipTest
    def test_create_sets_playlist_uri(self):
        pass

    @unittest.SkipTest
    def test_save_sets_playlist_uri(self):
        pass
