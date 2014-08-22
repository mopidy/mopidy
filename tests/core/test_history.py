from __future__ import unicode_literals

import unittest

from mopidy.core import History
from mopidy.models import Artist, Track


class PlaybackHistoryTest(unittest.TestCase):
    def setUp(self):
        self.tracks = [
            Track(uri='dummy1:a', name='foo',
                  artists=[Artist(name='foober'), Artist(name='barber')]),
            Track(uri='dummy2:a', name='foo'),
            Track(uri='dummy3:a', name='bar')
        ]
        self.history = History()

    def test_add_track(self):
        self.history.add(self.tracks[0])
        self.history.add(self.tracks[1])
        self.history.add(self.tracks[2])
        self.assertEqual(self.history.size, 3)

    def test_unsuitable_add(self):
        size = self.history.size
        self.history.add(self.tracks[0])
        self.history.add(object())
        self.history.add(self.tracks[1])
        self.assertEqual(self.history.size, size + 2)

    def test_history_sanity(self):
        track = self.tracks[0]
        self.history.add(track)
        stored_history = self.history.get_history()
        track_ref = stored_history[0][1]
        self.assertEqual(track_ref.uri, track.uri)
        self.assertIn(track.name, track_ref.name)
        if track.artists:
            for artist in track.artists:
                self.assertIn(artist.name, track_ref.name)
