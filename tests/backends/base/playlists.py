from __future__ import unicode_literals

import os
import shutil
import tempfile

import pykka

from mopidy import audio, core, settings
from mopidy.models import Playlist

from tests import unittest, path_to_data_dir


class PlaylistsControllerTest(object):
    def setUp(self):
        settings.LOCAL_PLAYLIST_PATH = tempfile.mkdtemp()
        settings.LOCAL_TAG_CACHE_FILE = path_to_data_dir('library_tag_cache')
        settings.LOCAL_MUSIC_PATH = path_to_data_dir('')

        self.audio = audio.DummyAudio.start().proxy()
        self.backend = self.backend_class.start(audio=self.audio).proxy()
        self.core = core.Core(backends=[self.backend])

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

        if os.path.exists(settings.LOCAL_PLAYLIST_PATH):
            shutil.rmtree(settings.LOCAL_PLAYLIST_PATH)

        settings.runtime.clear()

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

    @unittest.SkipTest
    def test_playlist_with_unknown_track(self):
        pass
