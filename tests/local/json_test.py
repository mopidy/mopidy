from __future__ import unicode_literals

import unittest

from mopidy.local import json
from mopidy.models import Ref


class BrowseCacheTest(unittest.TestCase):
    def setUp(self):
        self.uris = [b'local:track:foo/bar/song1',
                     b'local:track:foo/bar/song2',
                     b'local:track:foo/song3']
        self.cache = json._BrowseCache(self.uris)

    def test_lookup_root(self):
        expected = [Ref.directory(uri='/foo', name='foo')]
        self.assertEqual(expected, self.cache.lookup('/'))

    def test_lookup_foo(self):
        expected = [Ref.directory(uri='/foo/bar', name='bar'),
                    Ref.track(uri=self.uris[2], name='song3')]
        self.assertEqual(expected, self.cache.lookup('/foo'))

    def test_lookup_foo_bar(self):
        expected = [Ref.track(uri=self.uris[0], name='song1'),
                    Ref.track(uri=self.uris[1], name='song2')]
        self.assertEqual(expected, self.cache.lookup('/foo/bar'))

    def test_lookup_foo_baz(self):
        self.assertEqual([], self.cache.lookup('/foo/baz'))

    def test_lookup_normalize_slashes(self):
        expected = [Ref.track(uri=self.uris[0], name='song1'),
                    Ref.track(uri=self.uris[1], name='song2')]
        self.assertEqual(expected, self.cache.lookup('/foo//bar/'))
