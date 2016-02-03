from __future__ import absolute_import, unicode_literals

import unittest

import mock

from mopidy import backend, core
from mopidy.internal import deprecation
from mopidy.models import Image, Ref, SearchResult, Track


class BaseCoreLibraryTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        dummy1_root = Ref.directory(uri='dummy1:directory', name='dummy1')
        self.backend1 = mock.Mock()
        self.backend1.uri_schemes.get.return_value = ['dummy1']
        self.backend1.actor_ref.actor_class.__name__ = 'DummyBackend1'
        self.library1 = mock.Mock(spec=backend.LibraryProvider)
        self.library1.get_images.return_value.get.return_value = {}
        self.library1.root_directory.get.return_value = dummy1_root
        self.backend1.library = self.library1
        self.backend1.has_playlists.return_value.get.return_value = False

        dummy2_root = Ref.directory(uri='dummy2:directory', name='dummy2')
        self.backend2 = mock.Mock()
        self.backend2.uri_schemes.get.return_value = ['dummy2', 'du2']
        self.backend2.actor_ref.actor_class.__name__ = 'DummyBackend2'
        self.library2 = mock.Mock(spec=backend.LibraryProvider)
        self.library2.get_images.return_value.get.return_value = {}
        self.library2.root_directory.get.return_value = dummy2_root
        self.backend2.library = self.library2
        self.backend2.has_playlists.return_value.get.return_value = False

        # A backend without the optional library provider
        self.backend3 = mock.Mock()
        self.backend3.uri_schemes.get.return_value = ['dummy3']
        self.backend3.actor_ref.actor_class.__name__ = 'DummyBackend3'
        self.backend3.has_library.return_value.get.return_value = False
        self.backend3.has_library_browse.return_value.get.return_value = False

        self.core = core.Core(mixer=None, backends=[
            self.backend1, self.backend2, self.backend3])


# TODO: split by method
class CoreLibraryTest(BaseCoreLibraryTest):

    def test_get_images_returns_empty_dict_for_no_uris(self):
        self.assertEqual({}, self.core.library.get_images([]))

    def test_get_images_returns_empty_result_for_unknown_uri(self):
        result = self.core.library.get_images(['dummy4:track'])
        self.assertEqual({'dummy4:track': tuple()}, result)

    def test_get_images_returns_empty_result_for_library_less_uri(self):
        result = self.core.library.get_images(['dummy3:track'])
        self.assertEqual({'dummy3:track': tuple()}, result)

    def test_get_images_maps_uri_to_backend(self):
        self.core.library.get_images(['dummy1:track'])
        self.library1.get_images.assert_called_once_with(['dummy1:track'])
        self.library2.get_images.assert_not_called()

    def test_get_images_maps_uri_to_backends(self):
        self.core.library.get_images(['dummy1:track', 'dummy2:track'])
        self.library1.get_images.assert_called_once_with(['dummy1:track'])
        self.library2.get_images.assert_called_once_with(['dummy2:track'])

    def test_get_images_returns_images(self):
        self.library1.get_images.return_value.get.return_value = {
            'dummy1:track': [Image(uri='uri')]}

        result = self.core.library.get_images(['dummy1:track'])
        self.assertEqual({'dummy1:track': (Image(uri='uri'),)}, result)

    def test_get_images_merges_results(self):
        self.library1.get_images.return_value.get.return_value = {
            'dummy1:track': [Image(uri='uri1')]}
        self.library2.get_images.return_value.get.return_value = {
            'dummy2:track': [Image(uri='uri2')]}

        result = self.core.library.get_images(
            ['dummy1:track', 'dummy2:track', 'dummy3:track', 'dummy4:track'])
        expected = {'dummy1:track': (Image(uri='uri1'),),
                    'dummy2:track': (Image(uri='uri2'),),
                    'dummy3:track': tuple(), 'dummy4:track': tuple()}
        self.assertEqual(expected, result)

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
        self.library1.browse.return_value.get.return_value = [
            Ref.directory(uri='dummy1:directory:/foo/bar', name='bar'),
            Ref.track(uri='dummy1:track:/foo/baz.mp3', name='Baz'),
        ]

        self.core.library.browse('dummy1:directory:/foo')

        self.assertEqual(self.library1.browse.call_count, 1)
        self.assertEqual(self.library2.browse.call_count, 0)
        self.library1.browse.assert_called_with('dummy1:directory:/foo')

    def test_browse_dummy2_selects_dummy2_backend(self):
        self.library2.browse.return_value.get.return_value = [
            Ref.directory(uri='dummy2:directory:/bar/baz', name='quux'),
            Ref.track(uri='dummy2:track:/bar/foo.mp3', name='Baz'),
        ]

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
        self.library1.browse.return_value.get.return_value = [
            Ref.directory(uri='dummy1:directory:/foo/bar', name='Bar'),
            Ref.track(uri='dummy1:track:/foo/baz.mp3', name='Baz'),
        ]

        result = self.core.library.browse('dummy1:directory:/foo')
        self.assertEqual(result, [
            Ref.directory(uri='dummy1:directory:/foo/bar', name='Bar'),
            Ref.track(uri='dummy1:track:/foo/baz.mp3', name='Baz'),
        ])

    def test_lookup_fails_with_uri_and_uris_set(self):
        with self.assertRaises(ValueError):
            self.core.library.lookup('dummy1:a', ['dummy2:a'])

    def test_lookup_can_handle_uris(self):
        track1 = Track(uri='dummy1:a', name='abc')
        track2 = Track(uri='dummy2:a', name='def')

        self.library1.lookup().get.return_value = [track1]
        self.library2.lookup().get.return_value = [track2]

        result = self.core.library.lookup(uris=['dummy1:a', 'dummy2:a'])
        self.assertEqual(result, {'dummy2:a': [track2], 'dummy1:a': [track1]})

    def test_lookup_uris_returns_empty_list_for_dummy3_track(self):
        result = self.core.library.lookup(uris=['dummy3:a'])

        self.assertEqual(result, {'dummy3:a': []})
        self.assertFalse(self.library1.lookup.called)
        self.assertFalse(self.library2.lookup.called)

    def test_lookup_ignores_tracks_without_uri_set(self):
        track1 = Track(uri='dummy1:a', name='abc')
        track2 = Track()

        self.library1.lookup().get.return_value = [track1, track2]

        result = self.core.library.lookup(uris=['dummy1:a'])
        self.assertEqual(result, {'dummy1:a': [track1]})

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

        self.library1.refresh.return_value.get.assert_called_once_with()
        self.library2.refresh.return_value.get.assert_called_once_with()

    def test_search_combines_results_from_all_backends(self):
        track1 = Track(uri='dummy1:a')
        track2 = Track(uri='dummy2:a')
        result1 = SearchResult(tracks=[track1])
        result2 = SearchResult(tracks=[track2])

        self.library1.search.return_value.get.return_value = result1
        self.library2.search.return_value.get.return_value = result2

        result = self.core.library.search({'any': ['a']})

        self.assertIn(result1, result)
        self.assertIn(result2, result)
        self.library1.search.assert_called_once_with(
            query={'any': ['a']}, uris=None, exact=False)
        self.library2.search.assert_called_once_with(
            query={'any': ['a']}, uris=None, exact=False)

    def test_search_with_uris_selects_dummy1_backend(self):
        self.core.library.search(
            query={'any': ['a']}, uris=['dummy1:', 'dummy1:foo', 'dummy3:'])

        self.library1.search.assert_called_once_with(
            query={'any': ['a']}, uris=['dummy1:', 'dummy1:foo'], exact=False)
        self.assertFalse(self.library2.search.called)

    def test_search_with_uris_selects_both_backends(self):
        self.core.library.search(
            query={'any': ['a']}, uris=['dummy1:', 'dummy1:foo', 'dummy2:'])

        self.library1.search.assert_called_once_with(
            query={'any': ['a']}, uris=['dummy1:', 'dummy1:foo'], exact=False)
        self.library2.search.assert_called_once_with(
            query={'any': ['a']}, uris=['dummy2:'], exact=False)

    def test_search_filters_out_none(self):
        track1 = Track(uri='dummy1:a')
        result1 = SearchResult(tracks=[track1])

        self.library1.search.return_value.get.return_value = result1
        self.library2.search.return_value.get.return_value = None

        result = self.core.library.search({'any': ['a']})

        self.assertIn(result1, result)
        self.assertNotIn(None, result)
        self.library1.search.assert_called_once_with(
            query={'any': ['a']}, uris=None, exact=False)
        self.library2.search.assert_called_once_with(
            query={'any': ['a']}, uris=None, exact=False)

    def test_search_accepts_query_dict_instead_of_kwargs(self):
        track1 = Track(uri='dummy1:a')
        track2 = Track(uri='dummy2:a')
        result1 = SearchResult(tracks=[track1])
        result2 = SearchResult(tracks=[track2])

        self.library1.search.return_value.get.return_value = result1
        self.library2.search.return_value.get.return_value = result2

        result = self.core.library.search({'any': ['a']})

        self.assertIn(result1, result)
        self.assertIn(result2, result)
        self.library1.search.assert_called_once_with(
            query={'any': ['a']}, uris=None, exact=False)
        self.library2.search.assert_called_once_with(
            query={'any': ['a']}, uris=None, exact=False)

    def test_search_normalises_bad_queries(self):
        self.core.library.search({'any': 'foobar'})
        self.library1.search.assert_called_once_with(
            query={'any': ['foobar']}, uris=None, exact=False)


class DeprecatedFindExactCoreLibraryTest(BaseCoreLibraryTest):

    def run(self, result=None):
        with deprecation.ignore('core.library.find_exact'):
            return super(DeprecatedFindExactCoreLibraryTest, self).run(result)

    def test_find_exact_combines_results_from_all_backends(self):
        track1 = Track(uri='dummy1:a')
        track2 = Track(uri='dummy2:a')
        result1 = SearchResult(tracks=[track1])
        result2 = SearchResult(tracks=[track2])

        self.library1.search.return_value.get.return_value = result1
        self.library2.search.return_value.get.return_value = result2

        result = self.core.library.find_exact({'any': ['a']})

        self.assertIn(result1, result)
        self.assertIn(result2, result)
        self.library1.search.assert_called_once_with(
            query=dict(any=['a']), uris=None, exact=True)
        self.library2.search.assert_called_once_with(
            query=dict(any=['a']), uris=None, exact=True)

    def test_find_exact_with_uris_selects_dummy1_backend(self):
        self.core.library.find_exact(
            query={'any': ['a']}, uris=['dummy1:', 'dummy1:foo', 'dummy3:'])

        self.library1.search.assert_called_once_with(
            query={'any': ['a']}, uris=['dummy1:', 'dummy1:foo'], exact=True)
        self.assertFalse(self.library2.search.called)

    def test_find_exact_with_uris_selects_both_backends(self):
        self.core.library.find_exact(
            query={'any': ['a']}, uris=['dummy1:', 'dummy1:foo', 'dummy2:'])

        self.library1.search.assert_called_once_with(
            query={'any': ['a']}, uris=['dummy1:', 'dummy1:foo'], exact=True)
        self.library2.search.assert_called_once_with(
            query={'any': ['a']}, uris=['dummy2:'], exact=True)

    def test_find_exact_filters_out_none(self):
        track1 = Track(uri='dummy1:a')
        result1 = SearchResult(tracks=[track1])

        self.library1.search.return_value.get.return_value = result1
        self.library2.search.return_value.get.return_value = None

        result = self.core.library.find_exact({'any': ['a']})

        self.assertIn(result1, result)
        self.assertNotIn(None, result)
        self.library1.search.assert_called_once_with(
            query={'any': ['a']}, uris=None, exact=True)
        self.library2.search.assert_called_once_with(
            query={'any': ['a']}, uris=None, exact=True)

    def test_find_accepts_query_dict_instead_of_kwargs(self):
        track1 = Track(uri='dummy1:a')
        track2 = Track(uri='dummy2:a')
        result1 = SearchResult(tracks=[track1])
        result2 = SearchResult(tracks=[track2])

        self.library1.search.return_value.get.return_value = result1
        self.library2.search.return_value.get.return_value = result2

        result = self.core.library.find_exact({'any': ['a']})

        self.assertIn(result1, result)
        self.assertIn(result2, result)
        self.library1.search.assert_called_once_with(
            query={'any': ['a']}, uris=None, exact=True)
        self.library2.search.assert_called_once_with(
            query={'any': ['a']}, uris=None, exact=True)

    def test_find_exact_normalises_bad_queries(self):
        self.core.library.find_exact({'any': 'foobar'})

        self.library1.search.assert_called_once_with(
            query={'any': ['foobar']}, uris=None, exact=True)


class DeprecatedLookupCoreLibraryTest(BaseCoreLibraryTest):

    def run(self, result=None):
        with deprecation.ignore('core.library.lookup:uri_arg'):
            return super(DeprecatedLookupCoreLibraryTest, self).run(result)

    def test_lookup_selects_dummy1_backend(self):
        self.library1.lookup.return_value.get.return_value = []
        self.core.library.lookup('dummy1:a')

        self.library1.lookup.assert_called_once_with('dummy1:a')
        self.assertFalse(self.library2.lookup.called)

    def test_lookup_selects_dummy2_backend(self):
        self.library2.lookup.return_value.get.return_value = []
        self.core.library.lookup('dummy2:a')

        self.assertFalse(self.library1.lookup.called)
        self.library2.lookup.assert_called_once_with('dummy2:a')

    def test_lookup_uri_returns_empty_list_for_dummy3_track(self):
        result = self.core.library.lookup('dummy3:a')

        self.assertEqual(result, [])
        self.assertFalse(self.library1.lookup.called)
        self.assertFalse(self.library2.lookup.called)


class LegacyFindExactToSearchLibraryTest(unittest.TestCase):

    def run(self, result=None):
        with deprecation.ignore('core.library.find_exact'):
            return super(LegacyFindExactToSearchLibraryTest, self).run(result)

    def setUp(self):  # noqa: N802
        self.backend = mock.Mock()
        self.backend.actor_ref.actor_class.__name__ = 'DummyBackend'
        self.backend.uri_schemes.get.return_value = ['dummy']
        self.backend.library = mock.Mock(spec=backend.LibraryProvider)
        self.core = core.Core(mixer=None, backends=[self.backend])

    def test_core_find_exact_calls_backend_search_with_exact(self):
        self.core.library.find_exact(query={'any': ['a']})
        self.backend.library.search.assert_called_once_with(
            query=dict(any=['a']), uris=None, exact=True)

    def test_core_find_exact_handles_legacy_backend(self):
        self.backend.library.search.return_value.get.side_effect = TypeError
        self.core.library.find_exact(query={'any': ['a']})
        # We are just testing that this doesn't fail.

    def test_core_search_call_backend_search_with_exact(self):
        self.core.library.search(query={'any': ['a']})
        self.backend.library.search.assert_called_once_with(
            query=dict(any=['a']), uris=None, exact=False)

    def test_core_search_with_exact_call_backend_search_with_exact(self):
        self.core.library.search(query={'any': ['a']}, exact=True)
        self.backend.library.search.assert_called_once_with(
            query=dict(any=['a']), uris=None, exact=True)

    def test_core_search_with_handles_legacy_backend(self):
        self.backend.library.search.return_value.get.side_effect = TypeError
        self.core.library.search(query={'any': ['a']}, exact=True)
        # We are just testing that this doesn't fail.


class MockBackendCoreLibraryBase(unittest.TestCase):

    def setUp(self):  # noqa: N802
        dummy_root = Ref.directory(uri='dummy:directory', name='dummy')

        self.library = mock.Mock(spec=backend.LibraryProvider)
        self.library.root_directory.get.return_value = dummy_root

        self.backend = mock.Mock()
        self.backend.actor_ref.actor_class.__name__ = 'DummyBackend'
        self.backend.uri_schemes.get.return_value = ['dummy']
        self.backend.library = self.library

        self.core = core.Core(mixer=None, backends=[self.backend])


@mock.patch('mopidy.core.library.logger')
class BrowseBadBackendTest(MockBackendCoreLibraryBase):

    def test_backend_raises_exception_for_root(self, logger):
        # Might happen if root_directory is a property for some weird reason.
        self.library.root_directory.get.side_effect = Exception
        self.assertEqual([], self.core.library.browse(None))
        logger.exception.assert_called_with(mock.ANY, 'DummyBackend')

    def test_backend_returns_none_for_root(self, logger):
        self.library.root_directory.get.return_value = None
        self.assertEqual([], self.core.library.browse(None))
        logger.error.assert_called_with(mock.ANY, 'DummyBackend', mock.ANY)

    def test_backend_returns_wrong_type_for_root(self, logger):
        self.library.root_directory.get.return_value = 123
        self.assertEqual([], self.core.library.browse(None))
        logger.error.assert_called_with(mock.ANY, 'DummyBackend', mock.ANY)

    def test_backend_raises_exception_for_browse(self, logger):
        self.library.browse.return_value.get.side_effect = Exception
        self.assertEqual([], self.core.library.browse('dummy:directory'))
        logger.exception.assert_called_with(mock.ANY, 'DummyBackend')

    def test_backend_returns_wrong_type_for_browse(self, logger):
        self.library.browse.return_value.get.return_value = [123]
        self.assertEqual([], self.core.library.browse('dummy:directory'))
        logger.error.assert_called_with(mock.ANY, 'DummyBackend', mock.ANY)


@mock.patch('mopidy.core.library.logger')
class GetDistinctBadBackendTest(MockBackendCoreLibraryBase):

    def test_backend_raises_exception(self, logger):
        self.library.get_distinct.return_value.get.side_effect = Exception
        self.assertEqual(set(), self.core.library.get_distinct('artist'))
        logger.exception.assert_called_with(mock.ANY, 'DummyBackend')

    def test_backend_returns_none(self, logger):
        self.library.get_distinct.return_value.get.return_value = None
        self.assertEqual(set(), self.core.library.get_distinct('artist'))
        self.assertFalse(logger.error.called)

    def test_backend_returns_wrong_type(self, logger):
        self.library.get_distinct.return_value.get.return_value = 'abc'
        self.assertEqual(set(), self.core.library.get_distinct('artist'))
        logger.error.assert_called_with(mock.ANY, 'DummyBackend', mock.ANY)

    def test_backend_returns_iterable_containing_wrong_types(self, logger):
        self.library.get_distinct.return_value.get.return_value = [1, 2, 3]
        self.assertEqual(set(), self.core.library.get_distinct('artist'))
        logger.error.assert_called_with(mock.ANY, 'DummyBackend', mock.ANY)


@mock.patch('mopidy.core.library.logger')
class GetImagesBadBackendTest(MockBackendCoreLibraryBase):

    def test_backend_raises_exception(self, logger):
        uri = 'dummy:/1'
        self.library.get_images.return_value.get.side_effect = Exception
        self.assertEqual({uri: tuple()}, self.core.library.get_images([uri]))
        logger.exception.assert_called_with(mock.ANY, 'DummyBackend')

    def test_backend_returns_none(self, logger):
        uri = 'dummy:/1'
        self.library.get_images.return_value.get.return_value = None
        self.assertEqual({uri: tuple()}, self.core.library.get_images([uri]))
        self.assertFalse(logger.error.called)

    def test_backend_returns_wrong_type(self, logger):
        uri = 'dummy:/1'
        self.library.get_images.return_value.get.return_value = 'abc'
        self.assertEqual({uri: tuple()}, self.core.library.get_images([uri]))
        logger.error.assert_called_with(mock.ANY, 'DummyBackend', mock.ANY)

    def test_backend_returns_mapping_containing_wrong_types(self, logger):
        uri = 'dummy:/1'
        self.library.get_images.return_value.get.return_value = {uri: 'abc'}
        self.assertEqual({uri: tuple()}, self.core.library.get_images([uri]))
        logger.error.assert_called_with(mock.ANY, 'DummyBackend', mock.ANY)

    def test_backend_returns_mapping_containing_none(self, logger):
        uri = 'dummy:/1'
        self.library.get_images.return_value.get.return_value = {uri: None}
        self.assertEqual({uri: tuple()}, self.core.library.get_images([uri]))
        logger.error.assert_called_with(mock.ANY, 'DummyBackend', mock.ANY)

    def test_backend_returns_unknown_uri(self, logger):
        uri = 'dummy:/1'
        self.library.get_images.return_value.get.return_value = {'foo': []}
        self.assertEqual({uri: tuple()}, self.core.library.get_images([uri]))
        logger.error.assert_called_with(mock.ANY, 'DummyBackend', mock.ANY)


@mock.patch('mopidy.core.library.logger')
class LookupByUrisBadBackendTest(MockBackendCoreLibraryBase):

    def test_backend_raises_exception(self, logger):
        uri = 'dummy:/1'
        self.library.lookup.return_value.get.side_effect = Exception
        self.assertEqual({uri: []}, self.core.library.lookup(uris=[uri]))
        logger.exception.assert_called_with(mock.ANY, 'DummyBackend')

    def test_backend_returns_none(self, logger):
        uri = 'dummy:/1'
        self.library.lookup.return_value.get.return_value = None
        self.assertEqual({uri: []}, self.core.library.lookup(uris=[uri]))
        self.assertFalse(logger.error.called)

    def test_backend_returns_wrong_type(self, logger):
        uri = 'dummy:/1'
        self.library.lookup.return_value.get.return_value = 'abc'
        self.assertEqual({uri: []}, self.core.library.lookup(uris=[uri]))
        logger.error.assert_called_with(mock.ANY, 'DummyBackend', mock.ANY)

    def test_backend_returns_iterable_containing_wrong_types(self, logger):
        uri = 'dummy:/1'
        self.library.lookup.return_value.get.return_value = [123]
        self.assertEqual({uri: []}, self.core.library.lookup(uris=[uri]))
        logger.error.assert_called_with(mock.ANY, 'DummyBackend', mock.ANY)

    def test_backend_returns_none_with_uri(self, logger):
        uri = 'dummy:/1'
        self.library.lookup.return_value.get.return_value = None
        self.assertEqual([], self.core.library.lookup(uri))
        self.assertFalse(logger.error.called)

    def test_backend_returns_wrong_type_with_uri(self, logger):
        uri = 'dummy:/1'
        self.library.lookup.return_value.get.return_value = 'abc'
        self.assertEqual([], self.core.library.lookup(uri))
        logger.error.assert_called_with(mock.ANY, 'DummyBackend', mock.ANY)

    def test_backend_returns_iterable_wrong_types_with_uri(self, logger):
        uri = 'dummy:/1'
        self.library.lookup.return_value.get.return_value = [123]
        self.assertEqual([], self.core.library.lookup(uri))
        logger.error.assert_called_with(mock.ANY, 'DummyBackend', mock.ANY)


@mock.patch('mopidy.core.library.logger')
class RefreshBadBackendTest(MockBackendCoreLibraryBase):

    def test_backend_raises_exception(self, logger):
        self.library.refresh.return_value.get.side_effect = Exception
        self.core.library.refresh()
        logger.exception.assert_called_with(mock.ANY, 'DummyBackend')

    def test_backend_raises_exception_with_uri(self, logger):
        self.library.refresh.return_value.get.side_effect = Exception
        self.core.library.refresh('dummy:/1')
        logger.exception.assert_called_with(mock.ANY, 'DummyBackend')


@mock.patch('mopidy.core.library.logger')
class SearchBadBackendTest(MockBackendCoreLibraryBase):

    def test_backend_raises_exception(self, logger):
        self.library.search.return_value.get.side_effect = Exception
        self.assertEqual([], self.core.library.search(query={'any': ['foo']}))
        logger.exception.assert_called_with(mock.ANY, 'DummyBackend')

    def test_backend_raises_lookuperror(self, logger):
        # TODO: is this behavior desired? Do we need to continue handling
        # LookupError case specially.
        self.library.search.return_value.get.side_effect = LookupError
        with self.assertRaises(LookupError):
            self.core.library.search(query={'any': ['foo']})

    def test_backend_returns_none(self, logger):
        self.library.search.return_value.get.return_value = None
        self.assertEqual([], self.core.library.search(query={'any': ['foo']}))
        self.assertFalse(logger.error.called)

    def test_backend_returns_wrong_type(self, logger):
        self.library.search.return_value.get.return_value = 'abc'
        self.assertEqual([], self.core.library.search(query={'any': ['foo']}))
        logger.error.assert_called_with(mock.ANY, 'DummyBackend', mock.ANY)
