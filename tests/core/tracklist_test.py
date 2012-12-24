from __future__ import unicode_literals

from mopidy.core import Core
from mopidy.models import Track

from tests import unittest


class TracklistTest(unittest.TestCase):
    def setUp(self):
        self.tracks = [
            Track(uri='a', name='foo'),
            Track(uri='b', name='foo'),
            Track(uri='c', name='bar')
        ]
        self.core = Core(audio=None, backends=[])
        self.tl_tracks = self.core.tracklist.add(self.tracks)

    def test_remove_removes_tl_tracks_matching_query(self):
        tl_tracks = self.core.tracklist.remove(name='foo')

        self.assertEqual(2, len(tl_tracks))
        self.assertListEqual(self.tl_tracks[:2], tl_tracks)

        self.assertEqual(1, self.core.tracklist.length)
        self.assertListEqual(self.tl_tracks[2:], self.core.tracklist.tl_tracks)

    def test_remove_works_with_dict_instead_of_kwargs(self):
        tl_tracks = self.core.tracklist.remove({'name': 'foo'})

        self.assertEqual(2, len(tl_tracks))
        self.assertListEqual(self.tl_tracks[:2], tl_tracks)

        self.assertEqual(1, self.core.tracklist.length)
        self.assertListEqual(self.tl_tracks[2:], self.core.tracklist.tl_tracks)

    def test_filter_returns_tl_tracks_matching_query(self):
        tl_tracks = self.core.tracklist.filter(name='foo')

        self.assertEqual(2, len(tl_tracks))
        self.assertListEqual(self.tl_tracks[:2], tl_tracks)

    def test_filter_works_with_dict_instead_of_kwargs(self):
        tl_tracks = self.core.tracklist.filter({'name': 'foo'})

        self.assertEqual(2, len(tl_tracks))
        self.assertListEqual(self.tl_tracks[:2], tl_tracks)

    # TODO Extract tracklist tests from the base backend tests
