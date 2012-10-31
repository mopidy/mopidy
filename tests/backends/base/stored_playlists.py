import os
import shutil
import tempfile

import mock
import pykka

from mopidy import audio, core, settings
from mopidy.models import Playlist

from tests import unittest, path_to_data_dir


class StoredPlaylistsControllerTest(object):
    def setUp(self):
        settings.LOCAL_PLAYLIST_PATH = tempfile.mkdtemp()
        settings.LOCAL_TAG_CACHE_FILE = path_to_data_dir('library_tag_cache')
        settings.LOCAL_MUSIC_PATH = path_to_data_dir('')

        self.audio = mock.Mock(spec=audio.Audio)
        self.backend = self.backend_class.start(audio=self.audio).proxy()
        self.core = core.Core(backends=[self.backend])
        self.stored = self.core.stored_playlists

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

        if os.path.exists(settings.LOCAL_PLAYLIST_PATH):
            shutil.rmtree(settings.LOCAL_PLAYLIST_PATH)

        settings.runtime.clear()

    def test_create_returns_playlist_with_name_set(self):
        playlist = self.stored.create('test')
        self.assertEqual(playlist.name, 'test')

    def test_create_returns_playlist_with_uri_set(self):
        playlist = self.stored.create('test')
        self.assert_(playlist.uri)

    def test_create_adds_playlist_to_playlists_collection(self):
        playlist = self.stored.create('test')
        self.assert_(self.stored.playlists)
        self.assertIn(playlist, self.stored.playlists)

    def test_playlists_empty_to_start_with(self):
        self.assert_(not self.stored.playlists)

    def test_delete_non_existant_playlist(self):
        self.stored.delete(Playlist())

    def test_delete_playlist(self):
        playlist = self.stored.create('test')
        self.stored.delete(playlist)
        self.assert_(not self.stored.playlists)

    def test_get_without_criteria(self):
        test = self.stored.get
        self.assertRaises(LookupError, test)

    def test_get_with_wrong_cirteria(self):
        test = lambda: self.stored.get(name='foo')
        self.assertRaises(LookupError, test)

    def test_get_with_right_criteria(self):
        playlist1 = self.stored.create('test')
        playlist2 = self.stored.get(name='test')
        self.assertEqual(playlist1, playlist2)

    def test_get_by_name_returns_unique_match(self):
        playlist = Playlist(name='b')
        self.backend.stored_playlists.playlists = [
            Playlist(name='a'), playlist]
        self.assertEqual(playlist, self.stored.get(name='b'))

    def test_get_by_name_returns_first_of_multiple_matches(self):
        playlist = Playlist(name='b')
        self.backend.stored_playlists.playlists = [
            playlist, Playlist(name='a'), Playlist(name='b')]
        try:
            self.stored.get(name='b')
            self.fail(u'Should raise LookupError if multiple matches')
        except LookupError as e:
            self.assertEqual(u'"name=b" match multiple playlists', e[0])

    def test_get_by_name_raises_keyerror_if_no_match(self):
        self.backend.stored_playlists.playlists = [
            Playlist(name='a'), Playlist(name='b')]
        try:
            self.stored.get(name='c')
            self.fail(u'Should raise LookupError if no match')
        except LookupError as e:
            self.assertEqual(u'"name=c" match no playlists', e[0])

    def test_lookup_finds_playlist_by_uri(self):
        original_playlist = self.stored.create('test')

        looked_up_playlist = self.stored.lookup(original_playlist.uri)

        self.assertEqual(original_playlist, looked_up_playlist)

    @unittest.SkipTest
    def test_refresh(self):
        pass

    def test_rename(self):
        playlist = self.stored.create('test')
        self.stored.rename(playlist, 'test2')
        self.stored.get(name='test2')

    def test_rename_unknown_playlist(self):
        self.stored.rename(Playlist(), 'test2')
        test = lambda: self.stored.get(name='test2')
        self.assertRaises(LookupError, test)

    def test_save_replaces_playlist_with_updated_playlist(self):
        playlist1 = self.stored.create('test1')
        self.assertIn(playlist1, self.stored.playlists)

        playlist2 = playlist1.copy(name='test2')
        self.stored.save(playlist2)
        self.assertNotIn(playlist1, self.stored.playlists)
        self.assertIn(playlist2, self.stored.playlists)

    @unittest.SkipTest
    def test_playlist_with_unknown_track(self):
        pass
