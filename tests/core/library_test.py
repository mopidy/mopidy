from __future__ import unicode_literals

import mock
import unittest

from mopidy.backends import base
from mopidy.core import Core
from mopidy.models import SearchResult, Track


class CoreLibraryTest(unittest.TestCase):
    def setUp(self):
        self.backend1 = mock.Mock()
        self.backend1.uri_schemes.get.return_value = ['dummy1']
        self.library1 = mock.Mock(spec=base.BaseLibraryProvider)
        self.backend1.library = self.library1

        self.backend2 = mock.Mock()
        self.backend2.uri_schemes.get.return_value = ['dummy2']
        self.library2 = mock.Mock(spec=base.BaseLibraryProvider)
        self.backend2.library = self.library2

        # A backend without the optional library provider
        self.backend3 = mock.Mock()
        self.backend3.uri_schemes.get.return_value = ['dummy3']
        self.backend3.has_library().get.return_value = False

        self.core = Core(audio=None, backends=[
            self.backend1, self.backend2, self.backend3])

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
