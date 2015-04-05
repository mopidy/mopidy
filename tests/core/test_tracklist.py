from __future__ import absolute_import, unicode_literals

import unittest

import mock

from mopidy import backend, core
from mopidy.models import Track
from mopidy.utils import deprecation


class TracklistTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.tracks = [
            Track(uri='dummy1:a', name='foo'),
            Track(uri='dummy1:b', name='foo'),
            Track(uri='dummy1:c', name='bar'),
        ]

        def lookup(uri):
            future = mock.Mock()
            future.get.return_value = [t for t in self.tracks if t.uri == uri]
            return future

        self.backend = mock.Mock()
        self.backend.uri_schemes.get.return_value = ['dummy1']
        self.library = mock.Mock(spec=backend.LibraryProvider)
        self.library.lookup.side_effect = lookup
        self.backend.library = self.library

        self.core = core.Core(mixer=None, backends=[self.backend])
        self.tl_tracks = self.core.tracklist.add(uris=[
            t.uri for t in self.tracks])

    def test_add_by_uri_looks_up_uri_in_library(self):
        self.library.lookup.reset_mock()
        self.core.tracklist.clear()

        with deprecation.ignore('core.tracklist.add:uri_arg'):
            tl_tracks = self.core.tracklist.add(uris=['dummy1:a'])

        self.library.lookup.assert_called_once_with('dummy1:a')
        self.assertEqual(1, len(tl_tracks))
        self.assertEqual(self.tracks[0], tl_tracks[0].track)
        self.assertEqual(tl_tracks, self.core.tracklist.tl_tracks[-1:])

    def test_add_by_uris_looks_up_uris_in_library(self):
        self.library.lookup.reset_mock()
        self.core.tracklist.clear()

        tl_tracks = self.core.tracklist.add(uris=[t.uri for t in self.tracks])

        self.library.lookup.assert_has_calls([
            mock.call('dummy1:a'),
            mock.call('dummy1:b'),
            mock.call('dummy1:c'),
        ])
        self.assertEqual(3, len(tl_tracks))
        self.assertEqual(self.tracks[0], tl_tracks[0].track)
        self.assertEqual(self.tracks[1], tl_tracks[1].track)
        self.assertEqual(self.tracks[2], tl_tracks[2].track)
        self.assertEqual(
            tl_tracks, self.core.tracklist.tl_tracks[-len(tl_tracks):])

    def test_remove_removes_tl_tracks_matching_query(self):
        tl_tracks = self.core.tracklist.remove(name=['foo'])

        self.assertEqual(2, len(tl_tracks))
        self.assertListEqual(self.tl_tracks[:2], tl_tracks)

        self.assertEqual(1, self.core.tracklist.length)
        self.assertListEqual(self.tl_tracks[2:], self.core.tracklist.tl_tracks)

    def test_remove_works_with_dict_instead_of_kwargs(self):
        tl_tracks = self.core.tracklist.remove({'name': ['foo']})

        self.assertEqual(2, len(tl_tracks))
        self.assertListEqual(self.tl_tracks[:2], tl_tracks)

        self.assertEqual(1, self.core.tracklist.length)
        self.assertListEqual(self.tl_tracks[2:], self.core.tracklist.tl_tracks)

    def test_filter_returns_tl_tracks_matching_query(self):
        tl_tracks = self.core.tracklist.filter(name=['foo'])

        self.assertEqual(2, len(tl_tracks))
        self.assertListEqual(self.tl_tracks[:2], tl_tracks)

    def test_filter_works_with_dict_instead_of_kwargs(self):
        tl_tracks = self.core.tracklist.filter({'name': ['foo']})

        self.assertEqual(2, len(tl_tracks))
        self.assertListEqual(self.tl_tracks[:2], tl_tracks)

    def test_filter_fails_if_values_isnt_iterable(self):
        with self.assertRaises(ValueError):
            self.core.tracklist.filter(tlid=3)

    def test_filter_fails_if_values_is_a_string(self):
        with self.assertRaises(ValueError):
            self.core.tracklist.filter(uri='a')

    # TODO Extract tracklist tests from the local backend tests
