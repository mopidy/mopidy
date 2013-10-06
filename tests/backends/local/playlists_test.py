from __future__ import unicode_literals

import os
import shutil
import tempfile
import unittest

from mopidy.backends.local import actor
from mopidy.models import Track

from tests import path_to_data_dir
from tests.backends.base.playlists import (
    PlaylistsControllerTest)
from tests.backends.local import generate_song


class LocalPlaylistsControllerTest(
        PlaylistsControllerTest, unittest.TestCase):

    backend_class = actor.LocalBackend
    config = {
        'local': {
            'media_dir': path_to_data_dir(''),
            'tag_cache_file': path_to_data_dir('library_tag_cache'),
        }
    }

    def setUp(self):
        self.config['local']['playlists_dir'] = tempfile.mkdtemp()
        self.playlists_dir = self.config['local']['playlists_dir']

        super(LocalPlaylistsControllerTest, self).setUp()

    def tearDown(self):
        super(LocalPlaylistsControllerTest, self).tearDown()

        if os.path.exists(self.playlists_dir):
            shutil.rmtree(self.playlists_dir)

    def test_created_playlist_is_persisted(self):
        path = os.path.join(self.playlists_dir, 'test.m3u')
        self.assertFalse(os.path.exists(path))

        self.core.playlists.create('test')
        self.assertTrue(os.path.exists(path))

    def test_create_slugifies_playlist_name(self):
        path = os.path.join(self.playlists_dir, 'test-foo-bar.m3u')
        self.assertFalse(os.path.exists(path))

        playlist = self.core.playlists.create('test FOO baR')
        self.assertEqual('test-foo-bar', playlist.name)
        self.assertTrue(os.path.exists(path))

    def test_create_slugifies_names_which_tries_to_change_directory(self):
        path = os.path.join(self.playlists_dir, 'test-foo-bar.m3u')
        self.assertFalse(os.path.exists(path))

        playlist = self.core.playlists.create('../../test FOO baR')
        self.assertEqual('test-foo-bar', playlist.name)
        self.assertTrue(os.path.exists(path))

    def test_saved_playlist_is_persisted(self):
        path1 = os.path.join(self.playlists_dir, 'test1.m3u')
        path2 = os.path.join(self.playlists_dir, 'test2-foo-bar.m3u')

        playlist = self.core.playlists.create('test1')

        self.assertTrue(os.path.exists(path1))
        self.assertFalse(os.path.exists(path2))

        playlist = playlist.copy(name='test2 FOO baR')
        playlist = self.core.playlists.save(playlist)

        self.assertEqual('test2-foo-bar', playlist.name)
        self.assertFalse(os.path.exists(path1))
        self.assertTrue(os.path.exists(path2))

    def test_deleted_playlist_is_removed(self):
        path = os.path.join(self.playlists_dir, 'test.m3u')
        self.assertFalse(os.path.exists(path))

        playlist = self.core.playlists.create('test')
        self.assertTrue(os.path.exists(path))

        self.core.playlists.delete(playlist.uri)
        self.assertFalse(os.path.exists(path))

    def test_playlist_contents_is_written_to_disk(self):
        track = Track(uri=generate_song(1))
        playlist = self.core.playlists.create('test')
        playlist_path = os.path.join(self.playlists_dir, 'test.m3u')
        playlist = playlist.copy(tracks=[track])
        playlist = self.core.playlists.save(playlist)

        with open(playlist_path) as playlist_file:
            contents = playlist_file.read()

        self.assertEqual(track.uri, contents.strip())

    def test_playlists_are_loaded_at_startup(self):
        track = Track(uri='local:track:path2')
        playlist = self.core.playlists.create('test')
        playlist = playlist.copy(tracks=[track])
        playlist = self.core.playlists.save(playlist)

        backend = self.backend_class(config=self.config, audio=self.audio)

        self.assert_(backend.playlists.playlists)
        self.assertEqual(
            'local:playlist:test', backend.playlists.playlists[0].uri)
        self.assertEqual(
            playlist.name, backend.playlists.playlists[0].name)
        self.assertEqual(
            track.uri, backend.playlists.playlists[0].tracks[0].uri)

    @unittest.SkipTest
    def test_santitising_of_playlist_filenames(self):
        pass

    @unittest.SkipTest
    def test_playlist_dir_is_created(self):
        pass
