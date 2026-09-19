from unittest import mock

import pykka
import pytest

import mopidy
from mopidy.core import Core, CoreListener
from mopidy.core._state_storage import (
    CoreControllersState,
    HistoryState,
    HistoryTrack,
    MixerControllerState,
    PlaybackControllerState,
    StoredState,
    TracklistControllerState,
)
from mopidy.models import Ref, TlTrack, Track
from mopidy.types import DurationMs, Percentage, PlaybackState, TracklistId, Uri
from tests import dummy_mixer


def make_backend_mock(
    actor_classname,
    *,
    uri_schemes,
    has_library,
    has_library_browse,
    has_playback,
    has_playlists,
):
    backend = mock.Mock()
    backend.actor_ref.actor_class.__name__ = actor_classname
    backend.uri_schemes.get.return_value = uri_schemes

    if isinstance(has_library, Exception):
        backend.has_library().get.side_effect = has_library
    else:
        backend.has_library().get.return_value = has_library

    if isinstance(has_library_browse, Exception):
        backend.has_library_browse().get.side_effect = has_library_browse
    else:
        backend.has_library_browse().get.return_value = has_library_browse

    if isinstance(has_playback, Exception):
        backend.has_playback().get.side_effect = has_playback
    else:
        backend.has_playback().get.return_value = has_playback

    if isinstance(has_playlists, Exception):
        backend.has_playlists().get.side_effect = has_playlists
    else:
        backend.has_playlists().get.return_value = has_playlists

    return backend


@pytest.fixture
def backend1():
    return make_backend_mock(
        "B1",
        uri_schemes=["dummy1"],
        has_library=True,
        has_library_browse=True,
        has_playback=False,
        has_playlists=False,
    )


@pytest.fixture
def backend2():
    return make_backend_mock(
        "B2",
        uri_schemes=["dummy2"],
        has_library=True,
        has_library_browse=False,
        has_playback=False,
        has_playlists=True,
    )


@pytest.fixture
def core(backend1, backend2):
    yield Core(
        config={},
        mixer=None,
        backends=[backend1, backend2],
    )
    pykka.ActorRegistry.stop_all()


def test_uri_schemes_has_uris_from_all_backends(core):
    result = core.get_uri_schemes()

    assert "dummy1" in result
    assert "dummy2" in result


def test_backend_lists_are_accurate(core, backend1, backend2):
    assert core.backends == [backend1, backend2]
    assert list(core.backends.with_library.keys()) == [
        "dummy1",
        "dummy2",
    ]
    assert list(core.backends.with_library_browse.keys()) == ["dummy1"]
    assert list(core.backends.with_playback.keys()) == []
    assert list(core.backends.with_playlists.keys()) == ["dummy2"]


def test_exclude_backend_from_sublists_on_error_when_first(backend1, backend2):
    backend3 = make_backend_mock(
        "B3",
        uri_schemes=["dummy3"],
        has_library=Exception(),
        has_library_browse=True,
        has_playback=False,
        has_playlists=False,
    )

    core = Core(
        config={},
        mixer=None,
        backends=[backend3, backend1, backend2],
    )

    assert core.backends == [backend1, backend2]
    assert list(core.backends.with_library.keys()) == ["dummy1", "dummy2"]
    assert list(core.backends.with_library_browse.keys()) == ["dummy1"]
    assert list(core.backends.with_playback.keys()) == []
    assert list(core.backends.with_playlists.keys()) == ["dummy2"]


def test_exclude_backend_from_sublists_on_error_when_not_first(backend1, backend2):
    backend3 = make_backend_mock(
        "B3",
        uri_schemes=["dummy3"],
        has_library=False,
        has_library_browse=True,
        has_playback=Exception(),
        has_playlists=False,
    )

    core = Core(
        config={},
        mixer=None,
        backends=[backend1, backend3, backend2],
    )

    assert core.backends == [backend1, backend2]
    assert list(core.backends.with_library.keys()) == ["dummy1", "dummy2"]
    assert list(core.backends.with_library_browse.keys()) == ["dummy1"]
    assert list(core.backends.with_playback.keys()) == []
    assert list(core.backends.with_playlists.keys()) == ["dummy2"]


def test_backends_with_colliding_uri_schemes_fails(backend1, backend2):
    backend2.uri_schemes.get.return_value = ["dummy1", "dummy2"]

    with pytest.raises(
        AssertionError,
        match="Cannot add URI scheme 'dummy1' for B2, it is already handled by B1",
    ):
        Core(
            config={},
            mixer=None,
            backends=[backend1, backend2],
        )


def test_version(core):
    assert core.get_version() == mopidy.__version__


def test_state_changed(core, mocker):
    listener_mock = mocker.patch(
        "mopidy.core._playback.CoreListener", spec=CoreListener
    )

    core.state_changed(None, PlaybackState.PAUSED, None)

    assert listener_mock.send.mock_calls == [
        mock.call(
            "playback_state_changed",
            old_state="stopped",
            new_state="paused",
        ),
    ]


@pytest.fixture
def state_file(tmp_path):
    state_file = tmp_path / "core" / "state.json.gz"
    state_file.parent.mkdir()
    return state_file


@pytest.fixture
def mixer():
    return dummy_mixer.create_proxy()


@pytest.fixture
def core_with_state_file(tmp_path, state_file, mixer):
    config = {
        "core": {
            "max_tracklist_length": 10000,
            "restore_state": True,
            "data_dir": str(tmp_path),
        },
    }

    yield Core(
        config=config,
        mixer=mixer,
        backends=[],
    )
    pykka.ActorRegistry.stop_all()


def test_save_state(core_with_state_file, state_file):
    core_with_state_file._teardown()

    assert state_file.is_file()
    reload_data = StoredState.load(state_file)
    data = StoredState(
        version=mopidy.__version__,
        state=CoreControllersState(
            tracklist=TracklistControllerState(
                repeat=False,
                random=False,
                consume=False,
                single=False,
                next_tlid=TracklistId(1),
            ),
            history=HistoryState(),
            playback=PlaybackControllerState(
                state=PlaybackState.STOPPED,
                time_position=DurationMs(0),
            ),
            mixer=MixerControllerState(),
        ),
    )
    assert data == reload_data


def test_load_state_no_file(core_with_state_file):
    core_with_state_file._setup()

    assert core_with_state_file.mixer.get_mute() is None
    assert core_with_state_file.mixer.get_volume() is None
    assert core_with_state_file.tracklist._next_tlid == 1
    assert core_with_state_file.tracklist.get_repeat() is False
    assert core_with_state_file.tracklist.get_random() is False
    assert core_with_state_file.tracklist.get_consume() is False
    assert core_with_state_file.tracklist.get_single() is False
    assert core_with_state_file.tracklist.get_length() == 0
    assert core_with_state_file.playback._start_paused is False
    assert core_with_state_file.playback._start_at_position is None
    assert core_with_state_file.history.get_length() == 0


def test_load_state_with_data(core_with_state_file, state_file):
    state = StoredState(
        version=mopidy.__version__,
        state=CoreControllersState(
            tracklist=TracklistControllerState(
                repeat=True,
                random=True,
                consume=False,
                single=False,
                tl_tracks=(
                    TlTrack(
                        tlid=TracklistId(12),
                        track=Track(uri=Uri("a:a")),
                    ),
                ),
                next_tlid=TracklistId(14),
            ),
            history=HistoryState(
                history=(
                    HistoryTrack(
                        timestamp=DurationMs(12),
                        track=Ref.track(uri=Uri("a:a"), name="a"),
                    ),
                    HistoryTrack(
                        timestamp=13,
                        track=Ref.track(uri=Uri("a:b"), name="b"),
                    ),
                ),
            ),
            playback=PlaybackControllerState(
                tlid=TracklistId(12),
                state=PlaybackState.PAUSED,
                time_position=DurationMs(432),
            ),
            mixer=MixerControllerState(mute=True, volume=Percentage(12)),
        ),
    )
    state.dump(state_file)

    core_with_state_file._setup()

    assert core_with_state_file.mixer.get_mute() is True
    assert core_with_state_file.mixer.get_volume() == 12
    assert core_with_state_file.tracklist._next_tlid == 14
    assert core_with_state_file.tracklist.get_repeat() is True
    assert core_with_state_file.tracklist.get_random() is True
    assert core_with_state_file.tracklist.get_consume() is False
    assert core_with_state_file.tracklist.get_single() is False
    assert core_with_state_file.tracklist.get_length() == 1
    assert core_with_state_file.playback._start_paused is True
    assert core_with_state_file.playback._start_at_position == 432
    assert core_with_state_file.history.get_length() == 2


def test_delete_state_file_on_restore(core_with_state_file, state_file):
    state = StoredState(
        version=mopidy.__version__,
        state=CoreControllersState(),
    )
    state.dump(state_file)
    assert state_file.is_file()

    core_with_state_file._setup()

    assert not state_file.exists()
