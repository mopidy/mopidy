from __future__ import absolute_import, unicode_literals

import unittest

from mopidy.local import json
from mopidy.models import Ref, Track

from tests import path_to_data_dir


class BrowseCacheTest(unittest.TestCase):
    maxDiff = None

    def setUp(self):  # noqa: N802
        self.uris = ['local:track:foo/bar/song1',
                     'local:track:foo/bar/song2',
                     'local:track:foo/baz/song3',
                     'local:track:foo/song4',
                     'local:track:song5']
        self.cache = json._BrowseCache(self.uris)

    def test_lookup_root(self):
        expected = [Ref.directory(uri='local:directory:foo', name='foo'),
                    Ref.track(uri='local:track:song5', name='song5')]
        self.assertEqual(expected, self.cache.lookup('local:directory'))

    def test_lookup_foo(self):
        expected = [Ref.directory(uri='local:directory:foo/bar', name='bar'),
                    Ref.directory(uri='local:directory:foo/baz', name='baz'),
                    Ref.track(uri=self.uris[3], name='song4')]
        result = self.cache.lookup('local:directory:foo')
        self.assertEqual(expected, result)

    def test_lookup_foo_bar(self):
        expected = [Ref.track(uri=self.uris[0], name='song1'),
                    Ref.track(uri=self.uris[1], name='song2')]
        self.assertEqual(
            expected, self.cache.lookup('local:directory:foo/bar'))

    def test_lookup_foo_baz(self):
        result = self.cache.lookup('local:directory:foo/unknown')
        self.assertEqual([], result)


class JsonLibraryTest(unittest.TestCase):

    config = {
        'core': {
            'data_dir': path_to_data_dir(''),
        },
        'local': {
            'media_dir': path_to_data_dir(''),
            'library': 'json',
        },
    }

    def setUp(self):  # noqa: N802
        self.library = json.JsonLibrary(self.config)

    def _create_tracks(self, count):
        for i in range(count):
            self.library.add(Track(uri='local:track:%d' % i))

    def test_search_should_default_limit_results(self):
        self._create_tracks(101)

        result = self.library.search()
        result_exact = self.library.search(exact=True)

        self.assertEqual(len(result.tracks), 100)
        self.assertEqual(len(result_exact.tracks), 100)

    def test_search_should_limit_results(self):
        self._create_tracks(100)

        result = self.library.search(limit=35)
        result_exact = self.library.search(exact=True, limit=35)

        self.assertEqual(len(result.tracks), 35)
        self.assertEqual(len(result_exact.tracks), 35)

    def test_search_should_offset_results(self):
        self._create_tracks(200)

        expected = self.library.search(limit=110).tracks[10:]
        expected_exact = self.library.search(exact=True, limit=110).tracks[10:]

        result = self.library.search(offset=10).tracks
        result_exact = self.library.search(offset=10, exact=True).tracks

        self.assertEqual(expected, result)
        self.assertEqual(expected_exact, result_exact)
