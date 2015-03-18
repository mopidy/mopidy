from __future__ import absolute_import, unicode_literals

import os
import shutil
import tempfile
import unittest

import pykka

from mopidy import core
from mopidy.m3u import actor
from mopidy.m3u.translator import playlist_uri_to_path
from mopidy.models import Playlist, Track

from tests import dummy_audio, path_to_data_dir
from tests.m3u import generate_song


class M3UPlaylistsProviderTest(unittest.TestCase):
    backend_class = actor.M3UBackend
    config = {
        'm3u': {
            'playlists_dir': path_to_data_dir(''),
        }
    }

    def setUp(self):  # noqa: N802
        self.config['m3u']['playlists_dir'] = tempfile.mkdtemp()
        self.playlists_dir = self.config['m3u']['playlists_dir']

        self.audio = dummy_audio.create_proxy()
        self.backend = actor.M3UBackend.start(
            config=self.config, audio=self.audio).proxy()
        self.core = core.Core(backends=[self.backend])

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()

        if os.path.exists(self.playlists_dir):
            shutil.rmtree(self.playlists_dir)

    def test_created_playlist_is_persisted(self):
        uri = 'm3u:test.m3u'
        path = playlist_uri_to_path(uri, self.playlists_dir)
        self.assertFalse(os.path.exists(path))

        playlist = self.core.playlists.create('test')
        self.assertEqual('test', playlist.name)
        self.assertEqual(uri, playlist.uri)
        self.assertTrue(os.path.exists(path))

    def test_create_sanitizes_playlist_name(self):
        playlist = self.core.playlists.create('../../test FOO baR')
        self.assertEqual('test FOO baR', playlist.name)
        path = playlist_uri_to_path(playlist.uri, self.playlists_dir)
        self.assertEqual(self.playlists_dir, os.path.dirname(path))
        self.assertTrue(os.path.exists(path))

    def test_saved_playlist_is_persisted(self):
        uri1 = 'm3u:test1.m3u'
        uri2 = 'm3u:test2.m3u'

        path1 = playlist_uri_to_path(uri1, self.playlists_dir)
        path2 = playlist_uri_to_path(uri2, self.playlists_dir)

        playlist = self.core.playlists.create('test1')
        self.assertEqual('test1', playlist.name)
        self.assertEqual(uri1, playlist.uri)
        self.assertTrue(os.path.exists(path1))
        self.assertFalse(os.path.exists(path2))

        playlist = self.core.playlists.save(playlist.copy(name='test2'))
        self.assertEqual('test2', playlist.name)
        self.assertEqual(uri2, playlist.uri)
        self.assertFalse(os.path.exists(path1))
        self.assertTrue(os.path.exists(path2))

    def test_deleted_playlist_is_removed(self):
        uri = 'm3u:test.m3u'
        path = playlist_uri_to_path(uri, self.playlists_dir)

        self.assertFalse(os.path.exists(path))

        playlist = self.core.playlists.create('test')
        self.assertEqual('test', playlist.name)
        self.assertEqual(uri, playlist.uri)
        self.assertTrue(os.path.exists(path))

        self.core.playlists.delete(playlist.uri)
        self.assertFalse(os.path.exists(path))

    def test_playlist_contents_is_written_to_disk(self):
        track = Track(uri=generate_song(1))
        playlist = self.core.playlists.create('test')
        playlist = self.core.playlists.save(playlist.copy(tracks=[track]))
        path = playlist_uri_to_path(playlist.uri, self.playlists_dir)

        with open(path) as f:
            contents = f.read()

        self.assertEqual(track.uri, contents.strip())

    def test_extended_playlist_contents_is_written_to_disk(self):
        track = Track(uri=generate_song(1), name='Test', length=60000)
        playlist = self.core.playlists.create('test')
        playlist = self.core.playlists.save(playlist.copy(tracks=[track]))
        path = playlist_uri_to_path(playlist.uri, self.playlists_dir)

        with open(path) as f:
            contents = f.read().splitlines()

        self.assertEqual(contents, ['#EXTM3U', '#EXTINF:60,Test', track.uri])

    def test_playlists_are_loaded_at_startup(self):
        track = Track(uri='dummy:track:path2')
        playlist = self.core.playlists.create('test')
        playlist = playlist.copy(tracks=[track])
        playlist = self.core.playlists.save(playlist)

        backend = self.backend_class(config=self.config, audio=self.audio)

        self.assert_(backend.playlists.playlists)
        self.assertEqual(
            playlist.uri, backend.playlists.playlists[0].uri)
        self.assertEqual(
            playlist.name, backend.playlists.playlists[0].name)
        self.assertEqual(
            track.uri, backend.playlists.playlists[0].tracks[0].uri)

    @unittest.SkipTest
    def test_santitising_of_playlist_filenames(self):
        pass

    @unittest.SkipTest
    def test_playlists_dir_is_created(self):
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
        self.core.playlists.delete('m3u:unknown')

    def test_delete_playlist_removes_it_from_the_collection(self):
        playlist = self.core.playlists.create('test')
        self.assertIn(playlist, self.core.playlists.playlists)

        self.core.playlists.delete(playlist.uri)

        self.assertNotIn(playlist, self.core.playlists.playlists)

    def test_delete_playlist_without_file(self):
        playlist = self.core.playlists.create('test')
        self.assertIn(playlist, self.core.playlists.playlists)

        path = playlist_uri_to_path(playlist.uri, self.playlists_dir)
        self.assertTrue(os.path.exists(path))

        os.remove(path)
        self.assertFalse(os.path.exists(path))

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

    def test_refresh(self):
        playlist = self.core.playlists.create('test')
        self.assertIn(playlist, self.core.playlists.playlists)

        self.core.playlists.refresh()

        self.assertIn(playlist, self.core.playlists.playlists)

    def test_save_replaces_existing_playlist_with_updated_playlist(self):
        playlist1 = self.core.playlists.create('test1')
        self.assertIn(playlist1, self.core.playlists.playlists)

        playlist2 = playlist1.copy(name='test2')
        playlist2 = self.core.playlists.save(playlist2)
        self.assertNotIn(playlist1, self.core.playlists.playlists)
        self.assertIn(playlist2, self.core.playlists.playlists)

    def test_create_replaces_existing_playlist_with_updated_playlist(self):
        track = Track(uri=generate_song(1))
        playlist1 = self.core.playlists.create('test')
        playlist1 = self.core.playlists.save(playlist1.copy(tracks=[track]))
        self.assertIn(playlist1, self.core.playlists.playlists)

        playlist2 = self.core.playlists.create('test')
        self.assertEqual(playlist1.uri, playlist2.uri)
        self.assertNotIn(playlist1, self.core.playlists.playlists)
        self.assertIn(playlist2, self.core.playlists.playlists)

    def test_save_playlist_with_new_uri(self):
        # you *should* not do this
        uri = 'm3u:test.m3u'
        playlist = self.core.playlists.save(Playlist(uri=uri))
        self.assertIn(playlist, self.core.playlists.playlists)
        self.assertEqual(uri, playlist.uri)
        self.assertEqual('test', playlist.name)
        path = playlist_uri_to_path(playlist.uri, self.playlists_dir)
        self.assertTrue(os.path.exists(path))

    def test_playlist_with_unknown_track(self):
        track = Track(uri='file:///dev/null')
        playlist = self.core.playlists.create('test')
        playlist = playlist.copy(tracks=[track])
        playlist = self.core.playlists.save(playlist)

        backend = self.backend_class(config=self.config, audio=self.audio)

        self.assert_(backend.playlists.playlists)
        self.assertEqual('m3u:test.m3u', backend.playlists.playlists[0].uri)
        self.assertEqual(
            playlist.name, backend.playlists.playlists[0].name)
        self.assertEqual(
            track.uri, backend.playlists.playlists[0].tracks[0].uri)

    def test_playlist_sort_order(self):
        def check_order(playlists, names):
            self.assertEqual(names, [playlist.name for playlist in playlists])

        self.core.playlists.create('c')
        self.core.playlists.create('a')
        self.core.playlists.create('b')

        check_order(self.core.playlists.playlists, ['a', 'b', 'c'])

        self.core.playlists.refresh()

        check_order(self.core.playlists.playlists, ['a', 'b', 'c'])

        playlist = self.core.playlists.lookup('m3u:a.m3u')
        playlist = playlist.copy(name='d')
        playlist = self.core.playlists.save(playlist)

        check_order(self.core.playlists.playlists, ['b', 'c', 'd'])

        self.core.playlists.delete('m3u:c.m3u')

        check_order(self.core.playlists.playlists, ['b', 'd'])
