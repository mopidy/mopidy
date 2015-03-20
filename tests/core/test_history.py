from __future__ import absolute_import, unicode_literals

import unittest

from mopidy.core import HistoryController
from mopidy.models import Artist, Track


class PlaybackHistoryTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.tracks = [
            Track(uri='dummy1:a', name='foo',
                  artists=[Artist(name='foober'), Artist(name='barber')]),
            Track(uri='dummy2:a', name='foo'),
            Track(uri='dummy3:a', name='bar')
        ]
        self.history = HistoryController()

    def test_add_track(self):
        self.history._add_track(self.tracks[0])
        self.assertEqual(self.history.get_length(), 1)

        self.history._add_track(self.tracks[1])
        self.assertEqual(self.history.get_length(), 2)

        self.history._add_track(self.tracks[2])
        self.assertEqual(self.history.get_length(), 3)

    def test_non_tracks_are_rejected(self):
        with self.assertRaises(TypeError):
            self.history._add_track(object())

        self.assertEqual(self.history.get_length(), 0)

    def test_history_entry_contents(self):
        track = self.tracks[0]
        self.history._add_track(track)

        result = self.history.get_history()
        (timestamp, ref) = result[0]

        self.assertIsInstance(timestamp, int)
        self.assertEqual(track.uri, ref.uri)
        self.assertIn(track.name, ref.name)
        for artist in track.artists:
            self.assertIn(artist.name, ref.name)
