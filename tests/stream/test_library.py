from __future__ import absolute_import, unicode_literals

import unittest

import gobject
gobject.threads_init()

import mock

import pygst
pygst.require('0.10')
import gst  # noqa: pygst magic is needed to import correct gst

from mopidy.models import Track
from mopidy.stream import actor
from mopidy.utils.path import path_to_uri

from tests import path_to_data_dir


class LibraryProviderTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.backend = mock.Mock()
        self.backend.uri_schemes = ['file']
        self.uri = path_to_uri(path_to_data_dir('song1.wav'))

    def test_lookup_ignores_unknown_scheme(self):
        library = actor.StreamLibraryProvider(self.backend, 1000, [], {})
        self.assertFalse(library.lookup('http://example.com'))

    def test_lookup_respects_blacklist(self):
        library = actor.StreamLibraryProvider(self.backend, 10, [self.uri], {})
        self.assertEqual([Track(uri=self.uri)], library.lookup(self.uri))

    def test_lookup_respects_blacklist_globbing(self):
        blacklist = [path_to_uri(path_to_data_dir('')) + '*']
        library = actor.StreamLibraryProvider(self.backend, 100, blacklist, {})
        self.assertEqual([Track(uri=self.uri)], library.lookup(self.uri))

    def test_lookup_converts_uri_metadata_to_track(self):
        library = actor.StreamLibraryProvider(self.backend, 100, [], {})
        self.assertEqual([Track(length=4406, uri=self.uri)],
                         library.lookup(self.uri))
