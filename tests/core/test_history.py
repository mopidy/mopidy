import unittest

from mopidy.core import TrackHistory

from mopidy.models import Track


class PlaybackHistoryTest(unittest.TestCase):
    def setUp(self):
        self.tracks = [
            Track(uri='dummy1:a', name='foo'),
            Track(uri='dummy2:a', name='foo'),
            Track(uri='dummy3:a', name='bar')
        ]
        self.history = TrackHistory()

    def test_add_track(self):
        self.history.add_track(self.tracks[0])
        self.assertEqual(self.history.get_history_size(), 1)

    def test_track_order(self):
        self.history.add_track(self.tracks[0])
        self.history.add_track(self.tracks[1])
        self.history.add_track(self.tracks[2])
        self.history.add_track(self.tracks[0])
        self.assertEqual(self.history.get_history_size(), 3)
        self.assertEqual(self.history.get_history()[0], self.tracks[0])