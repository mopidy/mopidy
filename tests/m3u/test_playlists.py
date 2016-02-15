# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import os
import platform
import shutil
import tempfile
import unittest

import pykka

from mopidy import core
from mopidy.internal import deprecation
from mopidy.m3u.backend import M3UBackend
from mopidy.models import Playlist, Track

from tests import dummy_audio, path_to_data_dir
from tests.m3u import generate_song


class M3UPlaylistsProviderTest(unittest.TestCase):
    backend_class = M3UBackend
    config = {
        'm3u': {
            'enabled': True,
            'base_dir': None,
            'default_encoding': 'latin-1',
            'default_extension': '.m3u',
            'playlists_dir': path_to_data_dir(''),
        }
    }

    def setUp(self):  # noqa: N802
        self.config['m3u']['playlists_dir'] = tempfile.mkdtemp()
        self.playlists_dir = self.config['m3u']['playlists_dir']
        self.base_dir = self.config['m3u']['base_dir'] or self.playlists_dir

        audio = dummy_audio.create_proxy()
        backend = M3UBackend.start(
            config=self.config, audio=audio).proxy()
        self.core = core.Core(backends=[backend])

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()

        if os.path.exists(self.playlists_dir):
            shutil.rmtree(self.playlists_dir)

    def test_created_playlist_is_persisted(self):
        uri = 'm3u:test.m3u'
        path = os.path.join(self.playlists_dir, b'test.m3u')
        self.assertFalse(os.path.exists(path))

        playlist = self.core.playlists.create('test')
        self.assertEqual('test', playlist.name)
        self.assertEqual(uri, playlist.uri)
        self.assertTrue(os.path.exists(path))

    def test_create_sanitizes_playlist_name(self):
        playlist = self.core.playlists.create('  ../../test FOO baR ')
        self.assertEqual('..|..|test FOO baR', playlist.name)
        path = os.path.join(self.playlists_dir, b'..|..|test FOO baR.m3u')
        self.assertEqual(self.playlists_dir, os.path.dirname(path))
        self.assertTrue(os.path.exists(path))

    def test_saved_playlist_is_persisted(self):
        uri1 = 'm3u:test1.m3u'
        uri2 = 'm3u:test2.m3u'

        path1 = os.path.join(self.playlists_dir, b'test1.m3u')
        path2 = os.path.join(self.playlists_dir, b'test2.m3u')

        playlist = self.core.playlists.create('test1')
        self.assertEqual('test1', playlist.name)
        self.assertEqual(uri1, playlist.uri)
        self.assertTrue(os.path.exists(path1))
        self.assertFalse(os.path.exists(path2))

        playlist = self.core.playlists.save(playlist.replace(name='test2'))
        self.assertEqual('test2', playlist.name)
        self.assertEqual(uri2, playlist.uri)
        self.assertFalse(os.path.exists(path1))
        self.assertTrue(os.path.exists(path2))

    def test_deleted_playlist_is_removed(self):
        uri = 'm3u:test.m3u'
        path = os.path.join(self.playlists_dir, b'test.m3u')

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
        playlist = self.core.playlists.save(playlist.replace(tracks=[track]))
        path = os.path.join(self.playlists_dir, b'test.m3u')

        with open(path) as f:
            contents = f.read()

        self.assertEqual(track.uri, contents.strip())

    def test_extended_playlist_contents_is_written_to_disk(self):
        track = Track(uri=generate_song(1), name='Test', length=60000)
        playlist = self.core.playlists.create('test')
        playlist = self.core.playlists.save(playlist.replace(tracks=[track]))
        path = os.path.join(self.playlists_dir, b'test.m3u')

        with open(path) as f:
            m3u = f.read().splitlines()

        self.assertEqual(['#EXTM3U', '#EXTINF:-1,Test', track.uri], m3u)

    def test_latin1_playlist_contents_is_written_to_disk(self):
        track = Track(uri=generate_song(1), name='Test\x9f', length=60000)
        playlist = self.core.playlists.create('test')
        playlist = self.core.playlists.save(playlist.copy(tracks=[track]))
        path = os.path.join(self.playlists_dir, b'test.m3u')

        with open(path, 'rb') as f:
            m3u = f.read().splitlines()
        self.assertEqual([b'#EXTM3U', b'#EXTINF:-1,Test\x9f', track.uri], m3u)

    def test_utf8_playlist_contents_is_replaced_and_written_to_disk(self):
        track = Track(uri=generate_song(1), name='Test\u07b4', length=60000)
        playlist = self.core.playlists.create('test')
        playlist = self.core.playlists.save(playlist.copy(tracks=[track]))
        path = os.path.join(self.playlists_dir, b'test.m3u')

        with open(path, 'rb') as f:
            m3u = f.read().splitlines()
        self.assertEqual([b'#EXTM3U', b'#EXTINF:-1,Test?', track.uri], m3u)

    def test_playlists_are_loaded_at_startup(self):
        track = Track(uri='dummy:track:path2')
        playlist = self.core.playlists.create('test')
        playlist = playlist.replace(tracks=[track])
        playlist = self.core.playlists.save(playlist)

        self.assertEqual(len(self.core.playlists.as_list()), 1)
        result = self.core.playlists.lookup(playlist.uri)
        self.assertEqual(playlist.uri, result.uri)
        self.assertEqual(playlist.name, result.name)
        self.assertEqual(track.uri, result.tracks[0].uri)

    def test_load_playlist_with_nonfilesystem_encoding_of_filename(self):
        path = os.path.join(self.playlists_dir, 'øæå.m3u'.encode('latin-1'))
        with open(path, 'wb+') as f:
            f.write(b'#EXTM3U\n')

        self.core.playlists.refresh()

        self.assertEqual(len(self.core.playlists.as_list()), 1)
        result = self.core.playlists.as_list()
        if platform.system() == 'Darwin':
            self.assertEqual('%F8%E6%E5', result[0].name)
        else:
            self.assertEqual('\ufffd\ufffd\ufffd', result[0].name)

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
        playlists = self.core.playlists.as_list()
        self.assertIn(playlist.uri, [ref.uri for ref in playlists])

    def test_as_list_empty_to_start_with(self):
        self.assertEqual(len(self.core.playlists.as_list()), 0)

    def test_delete_non_existant_playlist(self):
        self.core.playlists.delete('m3u:unknown')

    def test_delete_playlist_removes_it_from_the_collection(self):
        playlist = self.core.playlists.create('test')
        self.assertEqual(playlist, self.core.playlists.lookup(playlist.uri))

        self.core.playlists.delete(playlist.uri)

        self.assertIsNone(self.core.playlists.lookup(playlist.uri))

    def test_delete_playlist_without_file(self):
        playlist = self.core.playlists.create('test')
        self.assertEqual(playlist, self.core.playlists.lookup(playlist.uri))

        path = os.path.join(self.playlists_dir, b'test.m3u')
        self.assertTrue(os.path.exists(path))

        os.remove(path)
        self.assertFalse(os.path.exists(path))

        self.core.playlists.delete(playlist.uri)
        self.assertIsNone(self.core.playlists.lookup(playlist.uri))

    def test_lookup_finds_playlist_by_uri(self):
        original_playlist = self.core.playlists.create('test')

        looked_up_playlist = self.core.playlists.lookup(original_playlist.uri)

        self.assertEqual(original_playlist, looked_up_playlist)

    def test_refresh(self):
        playlist = self.core.playlists.create('test')
        self.assertEqual(playlist, self.core.playlists.lookup(playlist.uri))

        self.core.playlists.refresh()

        self.assertEqual(playlist, self.core.playlists.lookup(playlist.uri))

    def test_save_replaces_existing_playlist_with_updated_playlist(self):
        playlist1 = self.core.playlists.create('test1')
        self.assertEqual(playlist1, self.core.playlists.lookup(playlist1.uri))

        playlist2 = playlist1.replace(name='test2')
        playlist2 = self.core.playlists.save(playlist2)
        self.assertIsNone(self.core.playlists.lookup(playlist1.uri))
        self.assertEqual(playlist2, self.core.playlists.lookup(playlist2.uri))

    def test_create_replaces_existing_playlist_with_updated_playlist(self):
        track = Track(uri=generate_song(1))
        playlist1 = self.core.playlists.create('test')
        playlist1 = self.core.playlists.save(playlist1.replace(tracks=[track]))
        self.assertEqual(playlist1, self.core.playlists.lookup(playlist1.uri))

        playlist2 = self.core.playlists.create('test')
        self.assertEqual(playlist1.uri, playlist2.uri)
        self.assertNotEqual(
            playlist1, self.core.playlists.lookup(playlist1.uri))
        self.assertEqual(playlist2, self.core.playlists.lookup(playlist1.uri))

    def test_save_playlist_with_new_uri(self):
        uri = 'm3u:test.m3u'
        self.core.playlists.save(Playlist(uri=uri))
        path = os.path.join(self.playlists_dir, b'test.m3u')
        self.assertTrue(os.path.exists(path))

    def test_playlist_with_unknown_track(self):
        track = Track(uri='file:///dev/null')
        playlist = self.core.playlists.create('test')
        playlist = playlist.replace(tracks=[track])
        playlist = self.core.playlists.save(playlist)

        self.assertEqual(len(self.core.playlists.as_list()), 1)
        result = self.core.playlists.lookup('m3u:test.m3u')
        self.assertEqual('m3u:test.m3u', result.uri)
        self.assertEqual(playlist.name, result.name)
        self.assertEqual(track.uri, result.tracks[0].uri)

    def test_playlist_with_absolute_path(self):
        track = Track(uri='/tmp/test.mp3')
        filepath = b'/tmp/test.mp3'
        playlist = self.core.playlists.create('test')
        playlist = playlist.replace(tracks=[track])
        playlist = self.core.playlists.save(playlist)

        self.assertEqual(len(self.core.playlists.as_list()), 1)
        result = self.core.playlists.lookup('m3u:test.m3u')
        self.assertEqual('m3u:test.m3u', result.uri)
        self.assertEqual(playlist.name, result.name)
        self.assertEqual('file://' + filepath, result.tracks[0].uri)

    def test_playlist_with_relative_path(self):
        track = Track(uri='test.mp3')
        filepath = os.path.join(self.base_dir, b'test.mp3')
        playlist = self.core.playlists.create('test')
        playlist = playlist.replace(tracks=[track])
        playlist = self.core.playlists.save(playlist)

        self.assertEqual(len(self.core.playlists.as_list()), 1)
        result = self.core.playlists.lookup('m3u:test.m3u')
        self.assertEqual('m3u:test.m3u', result.uri)
        self.assertEqual(playlist.name, result.name)
        self.assertEqual('file://' + filepath, result.tracks[0].uri)

    def test_playlist_sort_order(self):
        def check_order(playlists, names):
            self.assertEqual(names, [playlist.name for playlist in playlists])

        self.core.playlists.create('c')
        self.core.playlists.create('a')
        self.core.playlists.create('b')

        check_order(self.core.playlists.as_list(), ['a', 'b', 'c'])

        self.core.playlists.refresh()

        check_order(self.core.playlists.as_list(), ['a', 'b', 'c'])

        playlist = self.core.playlists.lookup('m3u:a.m3u')
        playlist = playlist.replace(name='d')
        playlist = self.core.playlists.save(playlist)

        check_order(self.core.playlists.as_list(), ['b', 'c', 'd'])

        self.core.playlists.delete('m3u:c.m3u')

        check_order(self.core.playlists.as_list(), ['b', 'd'])

    def test_get_items_returns_item_refs(self):
        track = Track(uri='dummy:a', name='A', length=60000)
        playlist = self.core.playlists.create('test')
        playlist = self.core.playlists.save(playlist.replace(tracks=[track]))

        item_refs = self.core.playlists.get_items(playlist.uri)

        self.assertEqual(len(item_refs), 1)
        self.assertEqual(item_refs[0].type, 'track')
        self.assertEqual(item_refs[0].uri, 'dummy:a')
        self.assertEqual(item_refs[0].name, 'A')

    def test_get_items_of_unknown_playlist_returns_none(self):
        item_refs = self.core.playlists.get_items('dummy:unknown')

        self.assertIsNone(item_refs)


class M3UPlaylistsProviderBaseDirectoryTest(M3UPlaylistsProviderTest):

    def setUp(self):  # noqa: N802
        self.config['m3u']['base_dir'] = tempfile.mkdtemp()
        super(M3UPlaylistsProviderBaseDirectoryTest, self).setUp()


class DeprecatedM3UPlaylistsProviderTest(M3UPlaylistsProviderTest):

    def run(self, result=None):
        with deprecation.ignore(ids=['core.playlists.filter',
                                     'core.playlists.filter:kwargs_criteria',
                                     'core.playlists.get_playlists']):
            return super(DeprecatedM3UPlaylistsProviderTest, self).run(result)

    def test_filter_without_criteria(self):
        self.assertEqual(self.core.playlists.get_playlists(),
                         self.core.playlists.filter())

    def test_filter_with_wrong_criteria(self):
        self.assertEqual([], self.core.playlists.filter(name='foo'))

    def test_filter_with_right_criteria(self):
        playlist = self.core.playlists.create('test')
        playlists = self.core.playlists.filter(name='test')
        self.assertEqual([playlist], playlists)

    def test_filter_by_name_returns_single_match(self):
        self.core.playlists.create('a')
        playlist = self.core.playlists.create('b')

        self.assertEqual([playlist], self.core.playlists.filter(name='b'))

    def test_filter_by_name_returns_no_matches(self):
        self.core.playlists.create('a')
        self.core.playlists.create('b')

        self.assertEqual([], self.core.playlists.filter(name='c'))
