import unittest
from unittest import mock

import pytest
from mopidy import backend, core
from mopidy.internal.models import TracklistState
from mopidy.models import TlTrack, Track


class TracklistTest(unittest.TestCase):
    def setUp(self):
        config = {"core": {"max_tracklist_length": 10000}}

        self.tracks = [
            Track(uri="dummy1:a", name="foo"),
            Track(uri="dummy1:b", name="foo"),
            Track(uri="dummy1:c", name="bar"),
        ]

        def lookup_many(uris):
            future = mock.Mock()
            future.get.return_value = {
                uri: [t for t in self.tracks if t.uri == uri] for uri in uris
            }
            return future

        self.backend = mock.Mock()
        self.backend.uri_schemes.get.return_value = ["dummy1"]
        self.library = mock.Mock(spec=backend.LibraryProvider)
        self.library.lookup_many.side_effect = lookup_many
        self.backend.library = self.library

        self.core = core.Core(config, mixer=None, backends=[self.backend])
        self.tl_tracks = self.core.tracklist.add(uris=[t.uri for t in self.tracks])

    def test_add_by_uri_looks_up_uri_in_library(self):
        self.library.lookup_many.reset_mock()
        self.core.tracklist.clear()

        tl_tracks = self.core.tracklist.add(uris=["dummy1:a"])

        self.library.lookup_many.assert_called_once_with(["dummy1:a"])
        assert len(tl_tracks) == 1
        assert self.tracks[0] == tl_tracks[0].track
        assert tl_tracks == self.core.tracklist.get_tl_tracks()[(-1):]

    def test_add_by_uris_looks_up_uris_in_library(self):
        self.library.lookup_many.reset_mock()
        self.core.tracklist.clear()

        tl_tracks = self.core.tracklist.add(uris=[t.uri for t in self.tracks])

        self.library.lookup_many.assert_called_with(
            [
                "dummy1:a",
                "dummy1:b",
                "dummy1:c",
            ]
        )

        assert len(tl_tracks) == 3
        assert self.tracks[0] == tl_tracks[0].track
        assert self.tracks[1] == tl_tracks[1].track
        assert self.tracks[2] == tl_tracks[2].track
        assert tl_tracks == self.core.tracklist.get_tl_tracks()[(-len(tl_tracks)) :]

    def test_remove_removes_tl_tracks_matching_query(self):
        tl_tracks = self.core.tracklist.remove({"name": ["foo"]})

        assert len(tl_tracks) == 2
        self.assertListEqual(self.tl_tracks[:2], tl_tracks)

        assert self.core.tracklist.get_length() == 1
        self.assertListEqual(self.tl_tracks[2:], self.core.tracklist.get_tl_tracks())

    def test_remove_works_with_dict_instead_of_kwargs(self):
        tl_tracks = self.core.tracklist.remove({"name": ["foo"]})

        assert len(tl_tracks) == 2
        self.assertListEqual(self.tl_tracks[:2], tl_tracks)

        assert self.core.tracklist.get_length() == 1
        self.assertListEqual(self.tl_tracks[2:], self.core.tracklist.get_tl_tracks())

    def test_filter_returns_tl_tracks_matching_query(self):
        tl_tracks = self.core.tracklist.filter({"name": ["foo"]})

        assert len(tl_tracks) == 2
        self.assertListEqual(self.tl_tracks[:2], tl_tracks)

    def test_filter_works_with_dict_instead_of_kwargs(self):
        tl_tracks = self.core.tracklist.filter({"name": ["foo"]})

        assert len(tl_tracks) == 2
        self.assertListEqual(self.tl_tracks[:2], tl_tracks)

    def test_filter_fails_if_values_isnt_iterable(self):
        with pytest.raises(ValueError):
            self.core.tracklist.filter({"tlid": 3})

    def test_filter_fails_if_values_is_a_string(self):
        with pytest.raises(ValueError):
            self.core.tracklist.filter({"uri": "a"})

    # TODO Extract tracklist tests from the local backend tests


class TracklistIndexTest(unittest.TestCase):
    def setUp(self):
        config = {"core": {"max_tracklist_length": 10000}}

        self.tracks = [
            Track(uri="dummy1:a", name="foo"),
            Track(uri="dummy1:b", name="foo"),
            Track(uri="dummy1:c", name="bar"),
        ]

        def lookup(uris):
            return {u: [t for t in self.tracks if t.uri == u] for u in uris}

        self.core = core.Core(config, mixer=None, backends=[])
        self.core.library = mock.Mock(spec=core.LibraryController)
        self.core.library.lookup.side_effect = lookup

        self.core.playback = mock.Mock(spec=core.PlaybackController)

        self.tl_tracks = self.core.tracklist.add(uris=[t.uri for t in self.tracks])

    def test_index_returns_index_of_track(self):
        assert self.core.tracklist.index(self.tl_tracks[0]) == 0
        assert self.core.tracklist.index(self.tl_tracks[1]) == 1
        assert self.core.tracklist.index(self.tl_tracks[2]) == 2

    def test_index_returns_none_if_item_not_found(self):
        tl_track = TlTrack(0, Track())
        assert self.core.tracklist.index(tl_track) is None

    def test_index_returns_none_if_called_with_none(self):
        assert self.core.tracklist.index(None) is None

    def test_index_errors_out_for_invalid_tltrack(self):
        with pytest.raises(ValueError):
            self.core.tracklist.index("abc")

    def test_index_return_index_when_called_with_tlids(self):
        tl_tracks = self.tl_tracks
        assert self.core.tracklist.index(tlid=tl_tracks[0].tlid) == 0
        assert self.core.tracklist.index(tlid=tl_tracks[1].tlid) == 1
        assert self.core.tracklist.index(tlid=tl_tracks[2].tlid) == 2

    def test_index_returns_none_if_tlid_not_found(self):
        assert self.core.tracklist.index(tlid=123) is None

    def test_index_returns_none_if_called_with_tlid_none(self):
        assert self.core.tracklist.index(tlid=None) is None

    def test_index_errors_out_for_invalid_tlid(self):
        with pytest.raises(ValueError):
            self.core.tracklist.index(tlid=-1)

    def test_index_without_args_returns_current_tl_track_index(self):
        self.core.playback.get_current_tl_track.side_effect = [
            None,
            self.tl_tracks[0],
            self.tl_tracks[1],
            self.tl_tracks[2],
        ]

        assert self.core.tracklist.index() is None
        assert self.core.tracklist.index() == 0
        assert self.core.tracklist.index() == 1
        assert self.core.tracklist.index() == 2


class TracklistSaveLoadStateTest(unittest.TestCase):
    def setUp(self):
        config = {"core": {"max_tracklist_length": 10000}}

        self.tracks = [
            Track(uri="dummy1:a", name="foo"),
            Track(uri="dummy1:b", name="foo"),
            Track(uri="dummy1:c", name="bar"),
        ]

        self.tl_tracks = [
            TlTrack(tlid=4, track=Track(uri="first", name="First")),
            TlTrack(tlid=5, track=Track(uri="second", name="Second")),
            TlTrack(tlid=6, track=Track(uri="third", name="Third")),
            TlTrack(tlid=8, track=Track(uri="last", name="Last")),
        ]

        def lookup(uris):
            return {u: [t for t in self.tracks if t.uri == u] for u in uris}

        self.core = core.Core(config, mixer=None, backends=[])
        self.core.library = mock.Mock(spec=core.LibraryController)
        self.core.library.lookup.side_effect = lookup

        self.core.playback = mock.Mock(spec=core.PlaybackController)

    def test_save(self):
        tl_tracks = self.core.tracklist.add(uris=[t.uri for t in self.tracks])
        consume = True
        next_tlid = len(tl_tracks) + 1
        self.core.tracklist.set_consume(consume)
        assert self.core.tracklist._save_state() == TracklistState(
            consume=consume,
            repeat=False,
            single=False,
            random=False,
            next_tlid=next_tlid,
            tl_tracks=tuple(tl_tracks),
        )

    def test_load(self):
        old_version = self.core.tracklist.get_version()
        target = TracklistState(
            consume=False,
            repeat=True,
            single=True,
            random=False,
            next_tlid=12,
            tl_tracks=self.tl_tracks,
        )
        coverage = ["mode", "tracklist"]
        self.core.tracklist._load_state(target, coverage)
        assert self.core.tracklist.get_consume() is False
        assert self.core.tracklist.get_repeat() is True
        assert self.core.tracklist.get_single() is True
        assert self.core.tracklist.get_random() is False
        assert self.core.tracklist._next_tlid == 12
        assert self.core.tracklist.get_length() == 4
        assert self.tl_tracks == self.core.tracklist.get_tl_tracks()
        assert self.core.tracklist.get_version() > old_version

        # after load, adding more tracks must be possible
        self.core.tracklist.add(uris=[self.tracks[1].uri])
        assert self.core.tracklist._next_tlid == 13
        assert self.core.tracklist.get_length() == 5

    def test_load_mode_only(self):
        old_version = self.core.tracklist.get_version()
        target = TracklistState(
            consume=False,
            repeat=True,
            single=True,
            random=False,
            next_tlid=12,
            tl_tracks=self.tl_tracks,
        )
        coverage = ["mode"]
        self.core.tracklist._load_state(target, coverage)
        assert self.core.tracklist.get_consume() is False
        assert self.core.tracklist.get_repeat() is True
        assert self.core.tracklist.get_single() is True
        assert self.core.tracklist.get_random() is False
        assert self.core.tracklist._next_tlid == 1
        assert self.core.tracklist.get_length() == 0
        assert [] == self.core.tracklist.get_tl_tracks()
        assert self.core.tracklist.get_version() == old_version

    def test_load_tracklist_only(self):
        old_version = self.core.tracklist.get_version()
        target = TracklistState(
            consume=False,
            repeat=True,
            single=True,
            random=False,
            next_tlid=12,
            tl_tracks=self.tl_tracks,
        )
        coverage = ["tracklist"]
        self.core.tracklist._load_state(target, coverage)
        assert self.core.tracklist.get_consume() is False
        assert self.core.tracklist.get_repeat() is False
        assert self.core.tracklist.get_single() is False
        assert self.core.tracklist.get_random() is False
        assert self.core.tracklist._next_tlid == 12
        assert self.core.tracklist.get_length() == 4
        assert self.tl_tracks == self.core.tracklist.get_tl_tracks()
        assert self.core.tracklist.get_version() > old_version

    def test_load_invalid_type(self):
        with pytest.raises(TypeError):
            self.core.tracklist._load_state(11, None)

    def test_load_none(self):
        self.core.tracklist._load_state(None, None)
