from __future__ import unicode_literals

import mock
import unittest

from mopidy import backend, core
from mopidy.models import Ref, SearchResult, Track


class CoreLibraryTest(unittest.TestCase):
    def setUp(self):
        dummy1_root = Ref.directory(uri='dummy1:directory', name='dummy1')
        self.backend1 = mock.Mock()
        self.backend1.uri_schemes.get.return_value = ['dummy1']
        self.library1 = mock.Mock(spec=backend.LibraryProvider)
        self.library1.root_directory.get.return_value = dummy1_root
        self.backend1.library = self.library1

        dummy2_root = Ref.directory(uri='dummy2:directory', name='dummy2')
        self.backend2 = mock.Mock()
        self.backend2.uri_schemes.get.return_value = ['dummy2']
        self.library2 = mock.Mock(spec=backend.LibraryProvider)
        self.library2.root_directory.get.return_value = dummy2_root
        self.backend2.library = self.library2

        # A backend without the optional library provider
        self.backend3 = mock.Mock()
        self.backend3.uri_schemes.get.return_value = ['dummy3']
        self.backend3.has_library().get.return_value = False
        self.backend3.has_library_browse().get.return_value = False

        self.core = core.Core(audio=None, backends=[
            self.backend1, self.backend2, self.backend3])

    def test_browse_root_returns_dir_ref_for_each_lib_with_root_dir_name(self):
        result = self.core.library.browse(None)

        self.assertEqual(result, [
            Ref.directory(uri='dummy1:directory', name='dummy1'),
            Ref.directory(uri='dummy2:directory', name='dummy2'),
        ])
        self.assertFalse(self.library1.browse.called)
        self.assertFalse(self.library2.browse.called)
        self.assertFalse(self.backend3.library.browse.called)

    def test_browse_empty_string_returns_nothing(self):
        result = self.core.library.browse('')

        self.assertEqual(result, [])
        self.assertFalse(self.library1.browse.called)
        self.assertFalse(self.library2.browse.called)

    def test_browse_dummy1_selects_dummy1_backend(self):
        self.library1.browse().get.return_value = [
            Ref.directory(uri='dummy1:directory:/foo/bar', name='bar'),
            Ref.track(uri='dummy1:track:/foo/baz.mp3', name='Baz'),
        ]
        self.library1.browse.reset_mock()

        self.core.library.browse('dummy1:directory:/foo')

        self.assertEqual(self.library1.browse.call_count, 1)
        self.assertEqual(self.library2.browse.call_count, 0)
        self.library1.browse.assert_called_with('dummy1:directory:/foo')

    def test_browse_dummy2_selects_dummy2_backend(self):
        self.library2.browse().get.return_value = [
            Ref.directory(uri='dummy2:directory:/bar/baz', name='quux'),
            Ref.track(uri='dummy2:track:/bar/foo.mp3', name='Baz'),
        ]
        self.library2.browse.reset_mock()

        self.core.library.browse('dummy2:directory:/bar')

        self.assertEqual(self.library1.browse.call_count, 0)
        self.assertEqual(self.library2.browse.call_count, 1)
        self.library2.browse.assert_called_with('dummy2:directory:/bar')

    def test_browse_dummy3_returns_nothing(self):
        result = self.core.library.browse('dummy3:test')

        self.assertEqual(result, [])
        self.assertEqual(self.library1.browse.call_count, 0)
        self.assertEqual(self.library2.browse.call_count, 0)

    def test_browse_dir_returns_subdirs_and_tracks(self):
        self.library1.browse().get.return_value = [
            Ref.directory(uri='dummy1:directory:/foo/bar', name='Bar'),
            Ref.track(uri='dummy1:track:/foo/baz.mp3', name='Baz'),
        ]
        self.library1.browse.reset_mock()

        result = self.core.library.browse('dummy1:directory:/foo')
        self.assertEqual(result, [
            Ref.directory(uri='dummy1:directory:/foo/bar', name='Bar'),
            Ref.track(uri='dummy1:track:/foo/baz.mp3', name='Baz'),
        ])

    def test_lookup_selects_dummy1_backend(self):
        self.core.library.lookup('dummy1:a')

        self.library1.lookup.assert_called_once_with('dummy1:a')
        self.assertFalse(self.library2.lookup.called)

    def test_lookup_selects_dummy2_backend(self):
        self.core.library.lookup('dummy2:a')

        self.assertFalse(self.library1.lookup.called)
        self.library2.lookup.assert_called_once_with('dummy2:a')

    def test_lookup_returns_nothing_for_dummy3_track(self):
        result = self.core.library.lookup('dummy3:a')

        self.assertEqual(result, [])
        self.assertFalse(self.library1.lookup.called)
        self.assertFalse(self.library2.lookup.called)

    def test_refresh_with_uri_selects_dummy1_backend(self):
        self.core.library.refresh('dummy1:a')

        self.library1.refresh.assert_called_once_with('dummy1:a')
        self.assertFalse(self.library2.refresh.called)

    def test_refresh_with_uri_selects_dummy2_backend(self):
        self.core.library.refresh('dummy2:a')

        self.assertFalse(self.library1.refresh.called)
        self.library2.refresh.assert_called_once_with('dummy2:a')

    def test_refresh_with_uri_fails_silently_for_dummy3_uri(self):
        self.core.library.refresh('dummy3:a')

        self.assertFalse(self.library1.refresh.called)
        self.assertFalse(self.library2.refresh.called)

    def test_refresh_without_uri_calls_all_backends(self):
        self.core.library.refresh()

        self.library1.refresh.assert_called_once_with(None)
        self.library2.refresh.assert_called_once_with(None)

    def test_find_exact_combines_results_from_all_backends(self):
        track1 = Track(uri='dummy1:a')
        track2 = Track(uri='dummy2:a')
        result1 = SearchResult(tracks=[track1])
        result2 = SearchResult(tracks=[track2])

        self.library1.find_exact().get.return_value = result1
        self.library1.find_exact.reset_mock()
        self.library2.find_exact().get.return_value = result2
        self.library2.find_exact.reset_mock()

        result = self.core.library.find_exact(any=['a'])

        self.assertIn(result1, result)
        self.assertIn(result2, result)
        self.library1.find_exact.assert_called_once_with(
            query=dict(any=['a']), uris=None)
        self.library2.find_exact.assert_called_once_with(
            query=dict(any=['a']), uris=None)

    def test_find_exact_with_uris_selects_dummy1_backend(self):
        self.core.library.find_exact(
            any=['a'], uris=['dummy1:', 'dummy1:foo', 'dummy3:'])

        self.library1.find_exact.assert_called_once_with(
            query=dict(any=['a']), uris=['dummy1:', 'dummy1:foo'])
        self.assertFalse(self.library2.find_exact.called)

    def test_find_exact_with_uris_selects_both_backends(self):
        self.core.library.find_exact(
            any=['a'], uris=['dummy1:', 'dummy1:foo', 'dummy2:'])

        self.library1.find_exact.assert_called_once_with(
            query=dict(any=['a']), uris=['dummy1:', 'dummy1:foo'])
        self.library2.find_exact.assert_called_once_with(
            query=dict(any=['a']), uris=['dummy2:'])

    def test_find_exact_filters_out_none(self):
        track1 = Track(uri='dummy1:a')
        result1 = SearchResult(tracks=[track1])

        self.library1.find_exact().get.return_value = result1
        self.library1.find_exact.reset_mock()
        self.library2.find_exact().get.return_value = None
        self.library2.find_exact.reset_mock()

        result = self.core.library.find_exact(any=['a'])

        self.assertIn(result1, result)
        self.assertNotIn(None, result)
        self.library1.find_exact.assert_called_once_with(
            query=dict(any=['a']), uris=None)
        self.library2.find_exact.assert_called_once_with(
            query=dict(any=['a']), uris=None)

    def test_find_accepts_query_dict_instead_of_kwargs(self):
        track1 = Track(uri='dummy1:a')
        track2 = Track(uri='dummy2:a')
        result1 = SearchResult(tracks=[track1])
        result2 = SearchResult(tracks=[track2])

        self.library1.find_exact().get.return_value = result1
        self.library1.find_exact.reset_mock()
        self.library2.find_exact().get.return_value = result2
        self.library2.find_exact.reset_mock()

        result = self.core.library.find_exact(dict(any=['a']))

        self.assertIn(result1, result)
        self.assertIn(result2, result)
        self.library1.find_exact.assert_called_once_with(
            query=dict(any=['a']), uris=None)
        self.library2.find_exact.assert_called_once_with(
            query=dict(any=['a']), uris=None)

    def test_search_combines_results_from_all_backends(self):
        track1 = Track(uri='dummy1:a')
        track2 = Track(uri='dummy2:a')
        result1 = SearchResult(tracks=[track1])
        result2 = SearchResult(tracks=[track2])

        self.library1.search().get.return_value = result1
        self.library1.search.reset_mock()
        self.library2.search().get.return_value = result2
        self.library2.search.reset_mock()

        result = self.core.library.search(any=['a'])

        self.assertIn(result1, result)
        self.assertIn(result2, result)
        self.library1.search.assert_called_once_with(
            query=dict(any=['a']), uris=None)
        self.library2.search.assert_called_once_with(
            query=dict(any=['a']), uris=None)

    def test_search_with_uris_selects_dummy1_backend(self):
        self.core.library.search(
            query=dict(any=['a']), uris=['dummy1:', 'dummy1:foo', 'dummy3:'])

        self.library1.search.assert_called_once_with(
            query=dict(any=['a']), uris=['dummy1:', 'dummy1:foo'])
        self.assertFalse(self.library2.search.called)

    def test_search_with_uris_selects_both_backends(self):
        self.core.library.search(
            query=dict(any=['a']), uris=['dummy1:', 'dummy1:foo', 'dummy2:'])

        self.library1.search.assert_called_once_with(
            query=dict(any=['a']), uris=['dummy1:', 'dummy1:foo'])
        self.library2.search.assert_called_once_with(
            query=dict(any=['a']), uris=['dummy2:'])

    def test_search_filters_out_none(self):
        track1 = Track(uri='dummy1:a')
        result1 = SearchResult(tracks=[track1])

        self.library1.search().get.return_value = result1
        self.library1.search.reset_mock()
        self.library2.search().get.return_value = None
        self.library2.search.reset_mock()

        result = self.core.library.search(any=['a'])

        self.assertIn(result1, result)
        self.assertNotIn(None, result)
        self.library1.search.assert_called_once_with(
            query=dict(any=['a']), uris=None)
        self.library2.search.assert_called_once_with(
            query=dict(any=['a']), uris=None)

    def test_search_accepts_query_dict_instead_of_kwargs(self):
        track1 = Track(uri='dummy1:a')
        track2 = Track(uri='dummy2:a')
        result1 = SearchResult(tracks=[track1])
        result2 = SearchResult(tracks=[track2])

        self.library1.search().get.return_value = result1
        self.library1.search.reset_mock()
        self.library2.search().get.return_value = result2
        self.library2.search.reset_mock()

        result = self.core.library.search(dict(any=['a']))

        self.assertIn(result1, result)
        self.assertIn(result2, result)
        self.library1.search.assert_called_once_with(
            query=dict(any=['a']), uris=None)
        self.library2.search.assert_called_once_with(
            query=dict(any=['a']), uris=None)
