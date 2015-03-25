from __future__ import absolute_import, unicode_literals

import unittest

import mock

from mopidy import backend, core
from mopidy.models import Track


class TracklistTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.tracks = [
            Track(uri='dummy1:a', name='foo'),
            Track(uri='dummy1:b', name='foo'),
            Track(uri='dummy1:c', name='bar'),
        ]

        self.backend = mock.Mock()
        self.backend.uri_schemes.get.return_value = ['dummy1']
        self.library = mock.Mock(spec=backend.LibraryProvider)
        self.backend.library = self.library

        self.core = core.Core(mixer=None, backends=[self.backend])
        self.tl_tracks = self.core.tracklist.add(self.tracks)

    def test_add_by_uri_looks_up_uri_in_library(self):
        track = Track(uri='dummy1:x', name='x')
        self.library.lookup.return_value.get.return_value = [track]

        tl_tracks = self.core.tracklist.add(uri='dummy1:x')

        self.library.lookup.assert_called_once_with('dummy1:x')
        self.assertEqual(1, len(tl_tracks))
        self.assertEqual(track, tl_tracks[0].track)
        self.assertEqual(tl_tracks, self.core.tracklist.tl_tracks[-1:])

    def test_add_by_uris_looks_up_uris_in_library(self):
        track1 = Track(uri='dummy1:x', name='x')
        track2 = Track(uri='dummy1:y1', name='y1')
        track3 = Track(uri='dummy1:y2', name='y2')
        self.library.lookup.return_value.get.side_effect = [
            [track1], [track2, track3]]

        tl_tracks = self.core.tracklist.add(uris=['dummy1:x', 'dummy1:y'])

        self.library.lookup.assert_has_calls([
            mock.call('dummy1:x'),
            mock.call('dummy1:y'),
        ])
        self.assertEqual(3, len(tl_tracks))
        self.assertEqual(track1, tl_tracks[0].track)
        self.assertEqual(track2, tl_tracks[1].track)
        self.assertEqual(track3, tl_tracks[2].track)
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
