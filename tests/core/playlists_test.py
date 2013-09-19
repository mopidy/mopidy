from __future__ import unicode_literals

import mock
import unittest

from mopidy.backends import base
from mopidy.core import Core
from mopidy.models import Playlist, Track


class PlaylistsTest(unittest.TestCase):
    def setUp(self):
        self.backend1 = mock.Mock()
        self.backend1.uri_schemes.get.return_value = ['dummy1']
        self.sp1 = mock.Mock(spec=base.BasePlaylistsProvider)
        self.backend1.playlists = self.sp1

        self.backend2 = mock.Mock()
        self.backend2.uri_schemes.get.return_value = ['dummy2']
        self.sp2 = mock.Mock(spec=base.BasePlaylistsProvider)
        self.backend2.playlists = self.sp2

        # A backend without the optional playlists provider
        self.backend3 = mock.Mock()
        self.backend3.uri_schemes.get.return_value = ['dummy3']
        self.backend3.has_playlists().get.return_value = False
        self.backend3.playlists = None

        self.pl1a = Playlist(name='A', tracks=[Track(uri='dummy1:a')])
        self.pl1b = Playlist(name='B', tracks=[Track(uri='dummy1:b')])
        self.sp1.playlists.get.return_value = [self.pl1a, self.pl1b]

        self.pl2a = Playlist(name='A', tracks=[Track(uri='dummy2:a')])
        self.pl2b = Playlist(name='B', tracks=[Track(uri='dummy2:b')])
        self.sp2.playlists.get.return_value = [self.pl2a, self.pl2b]

        self.core = Core(audio=None, backends=[
            self.backend3, self.backend1, self.backend2])

    def test_get_playlists_combines_result_from_backends(self):
        result = self.core.playlists.playlists

        self.assertIn(self.pl1a, result)
        self.assertIn(self.pl1b, result)
        self.assertIn(self.pl2a, result)
        self.assertIn(self.pl2b, result)

    def test_get_playlists_includes_tracks_by_default(self):
        result = self.core.playlists.get_playlists()

        self.assertEqual(result[0].name, 'A')
        self.assertEqual(len(result[0].tracks), 1)
        self.assertEqual(result[1].name, 'B')
        self.assertEqual(len(result[1].tracks), 1)

    def test_get_playlist_can_strip_tracks_from_returned_playlists(self):
        result = self.core.playlists.get_playlists(include_tracks=False)

        self.assertEqual(result[0].name, 'A')
        self.assertEqual(len(result[0].tracks), 0)
        self.assertEqual(result[1].name, 'B')
        self.assertEqual(len(result[1].tracks), 0)

    def test_create_without_uri_scheme_uses_first_backend(self):
        playlist = Playlist()
        self.sp1.create().get.return_value = playlist
        self.sp1.reset_mock()

        result = self.core.playlists.create('foo')

        self.assertEqual(playlist, result)
        self.sp1.create.assert_called_once_with('foo')
        self.assertFalse(self.sp2.create.called)

    def test_create_with_uri_scheme_selects_the_matching_backend(self):
        playlist = Playlist()
        self.sp2.create().get.return_value = playlist
        self.sp2.reset_mock()

        result = self.core.playlists.create('foo', uri_scheme='dummy2')

        self.assertEqual(playlist, result)
        self.assertFalse(self.sp1.create.called)
        self.sp2.create.assert_called_once_with('foo')

    def test_create_with_unsupported_uri_scheme_uses_first_backend(self):
        playlist = Playlist()
        self.sp1.create().get.return_value = playlist
        self.sp1.reset_mock()

        result = self.core.playlists.create('foo', uri_scheme='dummy3')

        self.assertEqual(playlist, result)
        self.sp1.create.assert_called_once_with('foo')
        self.assertFalse(self.sp2.create.called)

    def test_delete_selects_the_dummy1_backend(self):
        self.core.playlists.delete('dummy1:a')

        self.sp1.delete.assert_called_once_with('dummy1:a')
        self.assertFalse(self.sp2.delete.called)

    def test_delete_selects_the_dummy2_backend(self):
        self.core.playlists.delete('dummy2:a')

        self.assertFalse(self.sp1.delete.called)
        self.sp2.delete.assert_called_once_with('dummy2:a')

    def test_delete_with_unknown_uri_scheme_does_nothing(self):
        self.core.playlists.delete('unknown:a')

        self.assertFalse(self.sp1.delete.called)
        self.assertFalse(self.sp2.delete.called)

    def test_delete_ignores_backend_without_playlist_support(self):
        self.core.playlists.delete('dummy3:a')

        self.assertFalse(self.sp1.delete.called)
        self.assertFalse(self.sp2.delete.called)

    def test_filter_returns_matching_playlists(self):
        result = self.core.playlists.filter(name='A')

        self.assertEqual(2, len(result))

    def test_filter_accepts_dict_instead_of_kwargs(self):
        result = self.core.playlists.filter({'name': 'A'})

        self.assertEqual(2, len(result))

    def test_lookup_selects_the_dummy1_backend(self):
        self.core.playlists.lookup('dummy1:a')

        self.sp1.lookup.assert_called_once_with('dummy1:a')
        self.assertFalse(self.sp2.lookup.called)

    def test_lookup_selects_the_dummy2_backend(self):
        self.core.playlists.lookup('dummy2:a')

        self.assertFalse(self.sp1.lookup.called)
        self.sp2.lookup.assert_called_once_with('dummy2:a')

    def test_lookup_track_in_backend_without_playlists_fails(self):
        result = self.core.playlists.lookup('dummy3:a')

        self.assertIsNone(result)
        self.assertFalse(self.sp1.lookup.called)
        self.assertFalse(self.sp2.lookup.called)

    def test_refresh_without_uri_scheme_refreshes_all_backends(self):
        self.core.playlists.refresh()

        self.sp1.refresh.assert_called_once_with()
        self.sp2.refresh.assert_called_once_with()

    def test_refresh_with_uri_scheme_refreshes_matching_backend(self):
        self.core.playlists.refresh(uri_scheme='dummy2')

        self.assertFalse(self.sp1.refresh.called)
        self.sp2.refresh.assert_called_once_with()

    def test_refresh_with_unknown_uri_scheme_refreshes_nothing(self):
        self.core.playlists.refresh(uri_scheme='foobar')

        self.assertFalse(self.sp1.refresh.called)
        self.assertFalse(self.sp2.refresh.called)

    def test_refresh_ignores_backend_without_playlist_support(self):
        self.core.playlists.refresh(uri_scheme='dummy3')

        self.assertFalse(self.sp1.refresh.called)
        self.assertFalse(self.sp2.refresh.called)

    def test_save_selects_the_dummy1_backend(self):
        playlist = Playlist(uri='dummy1:a')
        self.sp1.save().get.return_value = playlist
        self.sp1.reset_mock()

        result = self.core.playlists.save(playlist)

        self.assertEqual(playlist, result)
        self.sp1.save.assert_called_once_with(playlist)
        self.assertFalse(self.sp2.save.called)

    def test_save_selects_the_dummy2_backend(self):
        playlist = Playlist(uri='dummy2:a')
        self.sp2.save().get.return_value = playlist
        self.sp2.reset_mock()

        result = self.core.playlists.save(playlist)

        self.assertEqual(playlist, result)
        self.assertFalse(self.sp1.save.called)
        self.sp2.save.assert_called_once_with(playlist)

    def test_save_does_nothing_if_playlist_uri_is_unset(self):
        result = self.core.playlists.save(Playlist())

        self.assertIsNone(result)
        self.assertFalse(self.sp1.save.called)
        self.assertFalse(self.sp2.save.called)

    def test_save_does_nothing_if_playlist_uri_has_unknown_scheme(self):
        result = self.core.playlists.save(Playlist(uri='foobar:a'))

        self.assertIsNone(result)
        self.assertFalse(self.sp1.save.called)
        self.assertFalse(self.sp2.save.called)

    def test_save_ignores_backend_without_playlist_support(self):
        result = self.core.playlists.save(Playlist(uri='dummy3:a'))

        self.assertIsNone(result)
        self.assertFalse(self.sp1.save.called)
        self.assertFalse(self.sp2.save.called)
