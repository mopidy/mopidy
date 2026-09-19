import pytest

from mopidy.core import HistoryController
from mopidy.core._state_storage import HistoryState, HistoryTrack
from mopidy.models import Artist, Ref, Track


@pytest.fixture
def history():
    return HistoryController()


@pytest.fixture
def tracks():
    return [
        Track(
            uri="dummy1:a",
            name="foo",
            artists=[Artist(name="foober"), Artist(name="barber")],
        ),
        Track(uri="dummy2:a", name="foo"),
        Track(uri="dummy3:a", name="bar"),
        Track(uri="dummy4:a", name="foo", artists=[Artist(name=None)]),
    ]


def test_add_track(history, tracks):
    history._add_track(tracks[0])
    assert history.get_length() == 1

    history._add_track(tracks[1])
    assert history.get_length() == 2

    history._add_track(tracks[2])
    assert history.get_length() == 3


def test_non_tracks_are_rejected(history):
    with pytest.raises(TypeError):
        history._add_track(object())

    assert history.get_length() == 0


def test_history_entry_contents(history, tracks):
    track = tracks[0]
    history._add_track(track)

    result = history.get_history()
    (timestamp, ref) = result[0]

    assert isinstance(timestamp, int)
    assert track.uri == ref.uri
    assert track.name in ref.name
    for artist in track.artists:
        assert artist.name in ref.name


def test_track_artist_no_name(history, tracks):
    history._add_track(tracks[3])
    assert history.get_length() == 1


@pytest.fixture
def state_tracks():
    return [
        Track(uri="dummy1:a", name="foober"),
        Track(uri="dummy2:a", name="foo"),
        Track(uri="dummy3:a", name="bar"),
    ]


@pytest.fixture
def refs(state_tracks):
    return [Ref.track(uri=t.uri, name=t.name) for t in state_tracks]


def test_state_save(history, state_tracks, refs):
    history._add_track(state_tracks[2])
    history._add_track(state_tracks[1])

    value = history._save_state()

    assert len(value.history) == 2
    # last in, first out
    assert value.history[0].track == refs[1]
    assert value.history[1].track == refs[2]


def test_state_load(history, state_tracks, refs):
    state = HistoryState(
        history=[
            HistoryTrack(timestamp=34, track=refs[0]),
            HistoryTrack(timestamp=45, track=refs[2]),
            HistoryTrack(timestamp=56, track=refs[1]),
        ],
    )
    coverage = ["history"]
    history._load_state(state, coverage)

    hist = history.get_history()
    assert len(hist) == 3
    assert hist[0] == (34, refs[0])
    assert hist[1] == (45, refs[2])
    assert hist[2] == (56, refs[1])

    # after import, adding more tracks must be possible
    history._add_track(state_tracks[1])
    hist = history.get_history()
    assert len(hist) == 4
    assert hist[0][1] == refs[1]
    assert hist[1] == (34, refs[0])
    assert hist[2] == (45, refs[2])
    assert hist[3] == (56, refs[1])


def test_state_load_invalid_type(history):
    with pytest.raises(TypeError):
        history._load_state(11, None)


def test_state_load_none(history):
    history._load_state(None, None)
