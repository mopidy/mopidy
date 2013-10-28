from __future__ import unicode_literals

import os
import shutil
import tempfile
import unittest

import pykka

from mopidy import audio, core
from mopidy.backends.local import actor
from mopidy.models import Playlist, Track

from tests import path_to_data_dir
from tests.backends.local import generate_song


class LocalPlaylistsProviderTest(unittest.TestCase):
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

        self.audio = audio.DummyAudio.start().proxy()
        self.backend = actor.LocalBackend.start(
            config=self.config, audio=self.audio).proxy()
        self.core = core.Core(backends=[self.backend])

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

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

    def test_create_returns_playlist_with_name_set(self):
        playlist = self.core.playlists.create('test')
        self.assertEqual(playlist.name, 'test')

    def test_create_returns_playlist_with_uri_set(self):
        playlist = self.core.playlists.create('test')
        self.assert_(playlist.uri)

    def test_create_adds_playlist_to_playlists_collection(self):
        playlist = self.core.playlists.create('test')
        self.assert_(self.core.playlists.playlists)
        self.assertIn(playlist, self.core.playlists.playlists)

    def test_playlists_empty_to_start_with(self):
        self.assert_(not self.core.playlists.playlists)

    def test_delete_non_existant_playlist(self):
        self.core.playlists.delete('file:///unknown/playlist')

    def test_delete_playlist_removes_it_from_the_collection(self):
        playlist = self.core.playlists.create('test')
        self.assertIn(playlist, self.core.playlists.playlists)

        self.core.playlists.delete(playlist.uri)

        self.assertNotIn(playlist, self.core.playlists.playlists)

    def test_filter_without_criteria(self):
        self.assertEqual(
            self.core.playlists.playlists, self.core.playlists.filter())

    def test_filter_with_wrong_criteria(self):
        self.assertEqual([], self.core.playlists.filter(name='foo'))

    def test_filter_with_right_criteria(self):
        playlist = self.core.playlists.create('test')
        playlists = self.core.playlists.filter(name='test')
        self.assertEqual([playlist], playlists)

    def test_filter_by_name_returns_single_match(self):
        playlist = Playlist(name='b')
        self.backend.playlists.playlists = [Playlist(name='a'), playlist]
        self.assertEqual([playlist], self.core.playlists.filter(name='b'))

    def test_filter_by_name_returns_multiple_matches(self):
        playlist = Playlist(name='b')
        self.backend.playlists.playlists = [
            playlist, Playlist(name='a'), Playlist(name='b')]
        playlists = self.core.playlists.filter(name='b')
        self.assertIn(playlist, playlists)
        self.assertEqual(2, len(playlists))

    def test_filter_by_name_returns_no_matches(self):
        self.backend.playlists.playlists = [
            Playlist(name='a'), Playlist(name='b')]
        self.assertEqual([], self.core.playlists.filter(name='c'))

    def test_lookup_finds_playlist_by_uri(self):
        original_playlist = self.core.playlists.create('test')

        looked_up_playlist = self.core.playlists.lookup(original_playlist.uri)

        self.assertEqual(original_playlist, looked_up_playlist)

    @unittest.SkipTest
    def test_refresh(self):
        pass

    def test_save_replaces_existing_playlist_with_updated_playlist(self):
        playlist1 = self.core.playlists.create('test1')
        self.assertIn(playlist1, self.core.playlists.playlists)

        playlist2 = playlist1.copy(name='test2')
        playlist2 = self.core.playlists.save(playlist2)
        self.assertNotIn(playlist1, self.core.playlists.playlists)
        self.assertIn(playlist2, self.core.playlists.playlists)

    def test_playlist_with_unknown_track(self):
        track = Track(uri='file:///dev/null')
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
