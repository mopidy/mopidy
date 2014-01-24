from __future__ import unicode_literals

import unittest

from mopidy.local import json
from mopidy.models import Ref


class BrowseCacheTest(unittest.TestCase):
    maxDiff = None

    def setUp(self):
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
