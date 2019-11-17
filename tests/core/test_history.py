import unittest

from mopidy.core import HistoryController
from mopidy.internal.models import HistoryState, HistoryTrack
from mopidy.models import Artist, Ref, Track


class PlaybackHistoryTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.tracks = [
            Track(
                uri="dummy1:a",
                name="foo",
                artists=[Artist(name="foober"), Artist(name="barber")],
            ),
            Track(uri="dummy2:a", name="foo"),
            Track(uri="dummy3:a", name="bar"),
        ]
        self.history = HistoryController()

    def test_add_track(self):
        self.history._add_track(self.tracks[0])
        assert self.history.get_length() == 1

        self.history._add_track(self.tracks[1])
        assert self.history.get_length() == 2

        self.history._add_track(self.tracks[2])
        assert self.history.get_length() == 3

    def test_non_tracks_are_rejected(self):
        with self.assertRaises(TypeError):
            self.history._add_track(object())

        assert self.history.get_length() == 0

    def test_history_entry_contents(self):
        track = self.tracks[0]
        self.history._add_track(track)

        result = self.history.get_history()
        (timestamp, ref) = result[0]

        assert isinstance(timestamp, int)
        assert track.uri == ref.uri
        assert track.name in ref.name
        for artist in track.artists:
            assert artist.name in ref.name


class CoreHistorySaveLoadStateTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.tracks = [
            Track(uri="dummy1:a", name="foober"),
            Track(uri="dummy2:a", name="foo"),
            Track(uri="dummy3:a", name="bar"),
        ]

        self.refs = []
        for t in self.tracks:
            self.refs.append(Ref.track(uri=t.uri, name=t.name))

        self.history = HistoryController()

    def test_save(self):
        self.history._add_track(self.tracks[2])
        self.history._add_track(self.tracks[1])

        value = self.history._save_state()

        assert len(value.history) == 2
        # last in, first out
        assert value.history[0].track == self.refs[1]
        assert value.history[1].track == self.refs[2]

    def test_load(self):
        state = HistoryState(
            history=[
                HistoryTrack(timestamp=34, track=self.refs[0]),
                HistoryTrack(timestamp=45, track=self.refs[2]),
                HistoryTrack(timestamp=56, track=self.refs[1]),
            ]
        )
        coverage = ["history"]
        self.history._load_state(state, coverage)

        hist = self.history.get_history()
        assert len(hist) == 3
        assert hist[0] == (34, self.refs[0])
        assert hist[1] == (45, self.refs[2])
        assert hist[2] == (56, self.refs[1])

        # after import, adding more tracks must be possible
        self.history._add_track(self.tracks[1])
        hist = self.history.get_history()
        assert len(hist) == 4
        assert hist[0][1] == self.refs[1]
        assert hist[1] == (34, self.refs[0])
        assert hist[2] == (45, self.refs[2])
        assert hist[3] == (56, self.refs[1])

    def test_load_invalid_type(self):
        with self.assertRaises(TypeError):
            self.history._load_state(11, None)

    def test_load_none(self):
        self.history._load_state(None, None)
