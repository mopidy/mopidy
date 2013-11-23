from __future__ import unicode_literals

import mock
import unittest

from mopidy.backends import base
from mopidy.core import Core
from mopidy.models import Track


class TracklistTest(unittest.TestCase):
    def setUp(self):
        self.tracks = [
            Track(uri='dummy1:a', name='foo'),
            Track(uri='dummy1:b', name='foo'),
            Track(uri='dummy1:c', name='bar'),
        ]

        self.backend = mock.Mock()
        self.backend.uri_schemes.get.return_value = ['dummy1']
        self.library = mock.Mock(spec=base.BaseLibraryProvider)
        self.backend.library = self.library

        self.core = Core(audio=None, backends=[self.backend])
        self.tl_tracks = self.core.tracklist.add(self.tracks)

    def test_add_by_uri_looks_up_uri_in_library(self):
        track = Track(uri='dummy1:x', name='x')
        self.library.lookup().get.return_value = [track]
        self.library.lookup.reset_mock()

        tl_tracks = self.core.tracklist.add(uri='dummy1:x')

        self.library.lookup.assert_called_once_with('dummy1:x')
        self.assertEqual(1, len(tl_tracks))
        self.assertEqual(track, tl_tracks[0].track)
        self.assertEqual(tl_tracks, self.core.tracklist.tl_tracks[-1:])

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
        self.assertRaises(ValueError, self.core.tracklist.filter, tlid=3)

    def test_filter_fails_if_values_is_a_string(self):
        self.assertRaises(ValueError, self.core.tracklist.filter, uri='a')

    # TODO Extract tracklist tests from the base backend tests
