from __future__ import unicode_literals

import os

from mopidy import settings
from mopidy.backends.local import LocalBackend
from mopidy.models import Track
from mopidy.utils.path import path_to_uri

from tests import unittest, path_to_data_dir
from tests.backends.base.playlists import (
    PlaylistsControllerTest)
from tests.backends.local import generate_song


class LocalPlaylistsControllerTest(
        PlaylistsControllerTest, unittest.TestCase):

    backend_class = LocalBackend

    def setUp(self):
        settings.LOCAL_TAG_CACHE_FILE = path_to_data_dir('empty_tag_cache')
        super(LocalPlaylistsControllerTest, self).setUp()

    def tearDown(self):
        super(LocalPlaylistsControllerTest, self).tearDown()
        settings.runtime.clear()

    def test_created_playlist_is_persisted(self):
        path = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test.m3u')
        self.assertFalse(os.path.exists(path))

        self.core.playlists.create('test')
        self.assertTrue(os.path.exists(path))

    def test_create_slugifies_playlist_name(self):
        path = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test-foo-bar.m3u')
        self.assertFalse(os.path.exists(path))

        playlist = self.core.playlists.create('test FOO baR')
        self.assertEqual('test-foo-bar', playlist.name)
        self.assertTrue(os.path.exists(path))

    def test_create_slugifies_names_which_tries_to_change_directory(self):
        path = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test-foo-bar.m3u')
        self.assertFalse(os.path.exists(path))

        playlist = self.core.playlists.create('../../test FOO baR')
        self.assertEqual('test-foo-bar', playlist.name)
        self.assertTrue(os.path.exists(path))

    def test_saved_playlist_is_persisted(self):
        path1 = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test1.m3u')
        path2 = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test2-foo-bar.m3u')

        playlist = self.core.playlists.create('test1')

        self.assertTrue(os.path.exists(path1))
        self.assertFalse(os.path.exists(path2))

        playlist = playlist.copy(name='test2 FOO baR')
        playlist = self.core.playlists.save(playlist)

        self.assertEqual('test2-foo-bar', playlist.name)
        self.assertFalse(os.path.exists(path1))
        self.assertTrue(os.path.exists(path2))

    def test_deleted_playlist_is_removed(self):
        path = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test.m3u')
        self.assertFalse(os.path.exists(path))

        playlist = self.core.playlists.create('test')
        self.assertTrue(os.path.exists(path))

        self.core.playlists.delete(playlist.uri)
        self.assertFalse(os.path.exists(path))

    def test_playlist_contents_is_written_to_disk(self):
        track = Track(uri=generate_song(1))
        track_path = track.uri[len('file://'):]
        playlist = self.core.playlists.create('test')
        playlist_path = playlist.uri[len('file://'):]
        playlist = playlist.copy(tracks=[track])
        playlist = self.core.playlists.save(playlist)

        with open(playlist_path) as playlist_file:
            contents = playlist_file.read()

        self.assertEqual(track_path, contents.strip())

    def test_playlists_are_loaded_at_startup(self):
        playlist_path = os.path.join(settings.LOCAL_PLAYLIST_PATH, 'test.m3u')

        track = Track(uri=path_to_uri(path_to_data_dir('uri2')))
        playlist = self.core.playlists.create('test')
        playlist = playlist.copy(tracks=[track])
        playlist = self.core.playlists.save(playlist)

        backend = self.backend_class(audio=self.audio)

        self.assert_(backend.playlists.playlists)
        self.assertEqual(
            path_to_uri(playlist_path),
            backend.playlists.playlists[0].uri)
        self.assertEqual(
            playlist.name, backend.playlists.playlists[0].name)
        self.assertEqual(
            track.uri, backend.playlists.playlists[0].tracks[0].uri)

    @unittest.SkipTest
    def test_santitising_of_playlist_filenames(self):
        pass

    @unittest.SkipTest
    def test_playlist_folder_is_createad(self):
        pass
