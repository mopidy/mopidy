from __future__ import absolute_import, unicode_literals

import unittest

from mopidy import compat
from mopidy.core import HistoryController
from mopidy.internal.models import HistoryState, HistoryTrack
from mopidy.models import Artist, Ref, Track


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

        self.assertIsInstance(timestamp, compat.integer_types)
        self.assertEqual(track.uri, ref.uri)
        self.assertIn(track.name, ref.name)
        for artist in track.artists:
            self.assertIn(artist.name, ref.name)


class CoreHistorySaveLoadStateTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.tracks = [
            Track(uri='dummy1:a', name='foober'),
            Track(uri='dummy2:a', name='foo'),
            Track(uri='dummy3:a', name='bar')
        ]

        self.refs = []
        for t in self.tracks:
            self.refs.append(Ref.track(uri=t.uri, name=t.name))

        self.history = HistoryController()

    def test_save(self):
        self.history._add_track(self.tracks[2])
        self.history._add_track(self.tracks[1])

        value = self.history._save_state()

        self.assertEqual(len(value.history), 2)
        # last in, first out
        self.assertEqual(value.history[0].track, self.refs[1])
        self.assertEqual(value.history[1].track, self.refs[2])

    def test_load(self):
        state = HistoryState(history=[
            HistoryTrack(timestamp=34, track=self.refs[0]),
            HistoryTrack(timestamp=45, track=self.refs[2]),
            HistoryTrack(timestamp=56, track=self.refs[1])])
        coverage = ['history']
        self.history._load_state(state, coverage)

        hist = self.history.get_history()
        self.assertEqual(len(hist), 3)
        self.assertEqual(hist[0], (34, self.refs[0]))
        self.assertEqual(hist[1], (45, self.refs[2]))
        self.assertEqual(hist[2], (56, self.refs[1]))

        # after import, adding more tracks must be possible
        self.history._add_track(self.tracks[1])
        hist = self.history.get_history()
        self.assertEqual(len(hist), 4)
        self.assertEqual(hist[0][1], self.refs[1])
        self.assertEqual(hist[1], (34, self.refs[0]))
        self.assertEqual(hist[2], (45, self.refs[2]))
        self.assertEqual(hist[3], (56, self.refs[1]))

    def test_load_invalid_type(self):
        with self.assertRaises(TypeError):
            self.history._load_state(11, None)

    def test_load_none(self):
        self.history._load_state(None, None)
