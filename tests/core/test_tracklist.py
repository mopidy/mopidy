from unittest import mock

import pytest

from mopidy.backend import LibraryProvider
from mopidy.core import Core, LibraryController, PlaybackController
from mopidy.core._state_storage import TracklistControllerState
from mopidy.models import TlTrack, Track
from mopidy.types import TracklistId
from tests.factories import TrackFactory

CONFIG = {"core": {"max_tracklist_length": 10000}}


@pytest.fixture
def tracks():
    return [
        Track(uri="dummy1:a", name="foo"),
        Track(uri="dummy1:b", name="foo"),
        Track(uri="dummy1:c", name="bar"),
    ]


@pytest.fixture
def library(tracks):
    def lookup_many(uris):
        future = mock.Mock()
        future.get.return_value = {
            uri: [t for t in tracks if t.uri == uri] for uri in uris
        }
        return future

    library = mock.Mock(spec=LibraryProvider)
    library.lookup_many.side_effect = lookup_many
    return library


@pytest.fixture
def backend(library):
    backend = mock.Mock()
    backend.uri_schemes.get.return_value = ["dummy1"]
    backend.library = library
    return backend


@pytest.fixture
def core(backend):
    return Core(CONFIG, mixer=None, backends=[backend])


@pytest.fixture
def tl_tracks(core, tracks):
    return core.tracklist.add(uris=[t.uri for t in tracks])


def test_add_by_uri_looks_up_uri_in_library(core, library, tracks, tl_tracks):
    library.lookup_many.reset_mock()
    core.tracklist.clear()

    tl_tracks = core.tracklist.add(uris=["dummy1:a"])

    library.lookup_many.assert_called_once_with(["dummy1:a"])
    assert len(tl_tracks) == 1
    assert tracks[0] == tl_tracks[0].track
    assert tl_tracks == core.tracklist.get_tl_tracks()[(-1):]


def test_add_by_uris_looks_up_uris_in_library(core, library, tracks, tl_tracks):
    library.lookup_many.reset_mock()
    core.tracklist.clear()

    tl_tracks = core.tracklist.add(uris=[t.uri for t in tracks])

    library.lookup_many.assert_called_with(
        [
            "dummy1:a",
            "dummy1:b",
            "dummy1:c",
        ],
    )

    assert len(tl_tracks) == 3
    assert tracks[0] == tl_tracks[0].track
    assert tracks[1] == tl_tracks[1].track
    assert tracks[2] == tl_tracks[2].track
    assert tl_tracks == core.tracklist.get_tl_tracks()[(-len(tl_tracks)) :]


def test_remove_removes_tl_tracks_matching_query(core, tl_tracks):
    result = core.tracklist.remove({"name": ["foo"]})

    assert len(result) == 2
    assert tl_tracks[:2] == result

    assert core.tracklist.get_length() == 1
    assert tl_tracks[2:] == core.tracklist.get_tl_tracks()


def test_remove_works_with_dict_instead_of_kwargs(core, tl_tracks):
    result = core.tracklist.remove({"name": ["foo"]})

    assert len(result) == 2
    assert tl_tracks[:2] == result

    assert core.tracklist.get_length() == 1
    assert tl_tracks[2:] == core.tracklist.get_tl_tracks()


def test_filter_returns_tl_tracks_matching_query(core, tl_tracks):
    result = core.tracklist.filter({"name": ["foo"]})

    assert len(result) == 2
    assert tl_tracks[:2] == result


def test_filter_works_with_dict_instead_of_kwargs(core, tl_tracks):
    result = core.tracklist.filter({"name": ["foo"]})

    assert len(result) == 2
    assert tl_tracks[:2] == result


def test_filter_fails_if_values_isnt_iterable(core, tl_tracks):
    with pytest.raises(ValueError):
        core.tracklist.filter({"tlid": 3})


def test_filter_fails_if_values_is_a_string(core, tl_tracks):
    with pytest.raises(ValueError):
        core.tracklist.filter({"uri": "a"})


# TODO: Extract tracklist tests from the local backend tests


@pytest.fixture
def mocked_core(tracks):
    def lookup(uris):
        return {u: [t for t in tracks if t.uri == u] for u in uris}

    mocked_core = Core(CONFIG, mixer=None, backends=[])
    mocked_core.library = mock.Mock(spec=LibraryController)
    mocked_core.library.lookup.side_effect = lookup

    mocked_core.playback = mock.Mock(spec=PlaybackController)
    return mocked_core


@pytest.fixture
def index_tl_tracks(mocked_core, tracks):
    return mocked_core.tracklist.add(uris=[t.uri for t in tracks])


def test_index_returns_index_of_track(mocked_core, index_tl_tracks):
    assert mocked_core.tracklist.index(index_tl_tracks[0]) == 0
    assert mocked_core.tracklist.index(index_tl_tracks[1]) == 1
    assert mocked_core.tracklist.index(index_tl_tracks[2]) == 2


def test_index_returns_none_if_item_not_found(mocked_core, index_tl_tracks):
    tl_track = TlTrack(TracklistId(1), TrackFactory.build())
    assert mocked_core.tracklist.index(tl_track) is None


def test_index_returns_none_if_called_with_none(mocked_core, index_tl_tracks):
    assert mocked_core.tracklist.index(None) is None


def test_index_errors_out_for_invalid_tltrack(mocked_core, index_tl_tracks):
    with pytest.raises(ValueError):
        mocked_core.tracklist.index("abc")


def test_index_return_index_when_called_with_tlids(mocked_core, index_tl_tracks):
    tl_tracks = index_tl_tracks
    assert mocked_core.tracklist.index(tlid=tl_tracks[0].tlid) == 0
    assert mocked_core.tracklist.index(tlid=tl_tracks[1].tlid) == 1
    assert mocked_core.tracklist.index(tlid=tl_tracks[2].tlid) == 2


def test_index_returns_none_if_tlid_not_found(mocked_core, index_tl_tracks):
    assert mocked_core.tracklist.index(tlid=123) is None


def test_index_returns_none_if_called_with_tlid_none(mocked_core, index_tl_tracks):
    assert mocked_core.tracklist.index(tlid=None) is None


def test_index_errors_out_for_invalid_tlid(mocked_core, index_tl_tracks):
    with pytest.raises(ValueError):
        mocked_core.tracklist.index(tlid=-1)


def test_index_without_args_returns_current_tl_track_index(
    mocked_core, index_tl_tracks
):
    mocked_core.playback.get_current_tl_track.side_effect = [
        None,
        index_tl_tracks[0],
        index_tl_tracks[1],
        index_tl_tracks[2],
    ]

    assert mocked_core.tracklist.index() is None
    assert mocked_core.tracklist.index() == 0
    assert mocked_core.tracklist.index() == 1
    assert mocked_core.tracklist.index() == 2


@pytest.fixture
def state_tl_tracks():
    return [
        TlTrack(tlid=4, track=Track(uri="first", name="First")),
        TlTrack(tlid=5, track=Track(uri="second", name="Second")),
        TlTrack(tlid=6, track=Track(uri="third", name="Third")),
        TlTrack(tlid=8, track=Track(uri="last", name="Last")),
    ]


def test_save_load_state_save(mocked_core, tracks):
    tl_tracks = mocked_core.tracklist.add(uris=[t.uri for t in tracks])
    consume = True
    next_tlid = len(tl_tracks) + 1
    mocked_core.tracklist.set_consume(consume)
    assert mocked_core.tracklist._save_state() == TracklistControllerState(
        consume=consume,
        repeat=False,
        single=False,
        random=False,
        next_tlid=next_tlid,
        tl_tracks=tuple(tl_tracks),
    )


def test_save_load_state_load(mocked_core, tracks, state_tl_tracks):
    old_version = mocked_core.tracklist.get_version()
    target = TracklistControllerState(
        consume=False,
        repeat=True,
        single=True,
        random=False,
        next_tlid=12,
        tl_tracks=state_tl_tracks,
    )
    coverage = ["mode", "tracklist"]
    mocked_core.tracklist._load_state(target, coverage)
    assert mocked_core.tracklist.get_consume() is False
    assert mocked_core.tracklist.get_repeat() is True
    assert mocked_core.tracklist.get_single() is True
    assert mocked_core.tracklist.get_random() is False
    assert mocked_core.tracklist._next_tlid == 12
    assert mocked_core.tracklist.get_length() == 4
    assert state_tl_tracks == mocked_core.tracklist.get_tl_tracks()
    assert mocked_core.tracklist.get_version() > old_version

    # after load, adding more tracks must be possible
    mocked_core.tracklist.add(uris=[tracks[1].uri])
    assert mocked_core.tracklist._next_tlid == 13
    assert mocked_core.tracklist.get_length() == 5


def test_save_load_state_load_mode_only(mocked_core, state_tl_tracks):
    old_version = mocked_core.tracklist.get_version()
    target = TracklistControllerState(
        consume=False,
        repeat=True,
        single=True,
        random=False,
        next_tlid=12,
        tl_tracks=state_tl_tracks,
    )
    coverage = ["mode"]
    mocked_core.tracklist._load_state(target, coverage)
    assert mocked_core.tracklist.get_consume() is False
    assert mocked_core.tracklist.get_repeat() is True
    assert mocked_core.tracklist.get_single() is True
    assert mocked_core.tracklist.get_random() is False
    assert mocked_core.tracklist._next_tlid == 1
    assert mocked_core.tracklist.get_length() == 0
    assert mocked_core.tracklist.get_tl_tracks() == []
    assert mocked_core.tracklist.get_version() == old_version


def test_save_load_state_load_tracklist_only(mocked_core, state_tl_tracks):
    old_version = mocked_core.tracklist.get_version()
    target = TracklistControllerState(
        consume=False,
        repeat=True,
        single=True,
        random=False,
        next_tlid=12,
        tl_tracks=state_tl_tracks,
    )
    coverage = ["tracklist"]
    mocked_core.tracklist._load_state(target, coverage)
    assert mocked_core.tracklist.get_consume() is False
    assert mocked_core.tracklist.get_repeat() is False
    assert mocked_core.tracklist.get_single() is False
    assert mocked_core.tracklist.get_random() is False
    assert mocked_core.tracklist._next_tlid == 12
    assert mocked_core.tracklist.get_length() == 4
    assert state_tl_tracks == mocked_core.tracklist.get_tl_tracks()
    assert mocked_core.tracklist.get_version() > old_version


def test_save_load_state_load_invalid_type(mocked_core):
    with pytest.raises(TypeError):
        mocked_core.tracklist._load_state(11, None)


def test_save_load_state_load_none(mocked_core):
    mocked_core.tracklist._load_state(None, None)
