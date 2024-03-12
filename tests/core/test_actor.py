import pathlib
import shutil
import tempfile
import unittest
from unittest import mock

import mopidy
import pykka
import pytest
from mopidy.audio import PlaybackState
from mopidy.core import Core, CoreListener
from mopidy.internal import models, storage
from mopidy.models import Ref, TlTrack, Track

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


class CoreActorTest(unittest.TestCase):
    def setUp(self):
        self.backend1 = make_backend_mock(
            "B1",
            uri_schemes=["dummy1"],
            has_library=True,
            has_library_browse=True,
            has_playback=False,
            has_playlists=False,
        )
        self.backend2 = make_backend_mock(
            "B2",
            uri_schemes=["dummy2"],
            has_library=True,
            has_library_browse=False,
            has_playback=False,
            has_playlists=True,
        )

        self.core = Core(
            config={},
            mixer=None,
            backends=[self.backend1, self.backend2],
        )

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_uri_schemes_has_uris_from_all_backends(self):
        result = self.core.get_uri_schemes()

        assert "dummy1" in result
        assert "dummy2" in result

    def test_backend_lists_are_accurate(self):
        assert self.core.backends == [self.backend1, self.backend2]
        assert list(self.core.backends.with_library.keys()) == [
            "dummy1",
            "dummy2",
        ]
        assert list(self.core.backends.with_library_browse.keys()) == ["dummy1"]
        assert list(self.core.backends.with_playback.keys()) == []
        assert list(self.core.backends.with_playlists.keys()) == ["dummy2"]

    def test_exclude_backend_from_sublists_on_error_when_first(self):
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
            backends=[backend3, self.backend1, self.backend2],
        )

        assert core.backends == [self.backend1, self.backend2]
        assert list(core.backends.with_library.keys()) == ["dummy1", "dummy2"]
        assert list(core.backends.with_library_browse.keys()) == ["dummy1"]
        assert list(core.backends.with_playback.keys()) == []
        assert list(core.backends.with_playlists.keys()) == ["dummy2"]

    def test_exclude_backend_from_sublists_on_error_when_not_first(self):
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
            backends=[self.backend1, backend3, self.backend2],
        )

        assert core.backends == [self.backend1, self.backend2]
        assert list(core.backends.with_library.keys()) == ["dummy1", "dummy2"]
        assert list(core.backends.with_library_browse.keys()) == ["dummy1"]
        assert list(core.backends.with_playback.keys()) == []
        assert list(core.backends.with_playlists.keys()) == ["dummy2"]

    def test_backends_with_colliding_uri_schemes_fails(self):
        self.backend2.uri_schemes.get.return_value = ["dummy1", "dummy2"]

        with pytest.raises(
            AssertionError,
            match="Cannot add URI scheme 'dummy1' for B2, it is already handled by B1",
        ):
            Core(
                config={},
                mixer=None,
                backends=[self.backend1, self.backend2],
            )

    def test_version(self):
        assert self.core.get_version() == mopidy.__version__

    @mock.patch("mopidy.core.playback.listener.CoreListener", spec=CoreListener)
    def test_state_changed(self, listener_mock):
        self.core.state_changed(None, PlaybackState.PAUSED, None)

        assert listener_mock.send.mock_calls == [
            mock.call(
                "playback_state_changed",
                old_state="stopped",
                new_state="paused",
            ),
        ]


class CoreActorSaveLoadStateTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = pathlib.Path(self.temp_dir) / "core" / "state.json.gz"
        self.state_file.parent.mkdir()

        config = {
            "core": {
                "max_tracklist_length": 10000,
                "restore_state": True,
                "data_dir": self.temp_dir,
            }
        }

        self.mixer = dummy_mixer.create_proxy()
        self.core = Core(
            config=config,
            mixer=self.mixer,
            backends=[],
        )

    def tearDown(self):
        pykka.ActorRegistry.stop_all()
        shutil.rmtree(self.temp_dir)

    def test_save_state(self):
        self.core._teardown()

        assert self.state_file.is_file()
        reload_data = storage.load(self.state_file)
        data = models.StoredState(
            version=mopidy.__version__,
            state=models.CoreState(
                tracklist=models.TracklistState(
                    repeat=False,
                    random=False,
                    consume=False,
                    single=False,
                    next_tlid=1,
                ),
                history=models.HistoryState(),
                playback=models.PlaybackState(state="stopped", time_position=0),
                mixer=models.MixerState(),
            ),
        )
        assert data == reload_data

    def test_load_state_no_file(self):
        self.core._setup()

        assert self.core.mixer.get_mute() is None
        assert self.core.mixer.get_volume() is None
        assert self.core.tracklist._next_tlid == 1
        assert self.core.tracklist.get_repeat() is False
        assert self.core.tracklist.get_random() is False
        assert self.core.tracklist.get_consume() is False
        assert self.core.tracklist.get_single() is False
        assert self.core.tracklist.get_length() == 0
        assert self.core.playback._start_paused is False
        assert self.core.playback._start_at_position is None
        assert self.core.history.get_length() == 0

    def test_load_state_with_data(self):
        data = models.StoredState(
            version=mopidy.__version__,
            state=models.CoreState(
                tracklist=models.TracklistState(
                    repeat=True,
                    random=True,
                    consume=False,
                    single=False,
                    tl_tracks=[TlTrack(tlid=12, track=Track(uri="a:a"))],
                    next_tlid=14,
                ),
                history=models.HistoryState(
                    history=[
                        models.HistoryTrack(
                            timestamp=12,
                            track=Ref.track(uri="a:a", name="a"),
                        ),
                        models.HistoryTrack(
                            timestamp=13,
                            track=Ref.track(uri="a:b", name="b"),
                        ),
                    ]
                ),
                playback=models.PlaybackState(
                    tlid=12,
                    state="paused",
                    time_position=432,
                ),
                mixer=models.MixerState(
                    volume=12,
                    mute=True,
                ),
            ),
        )
        storage.dump(self.state_file, data)

        self.core._setup()

        assert self.core.mixer.get_mute() is True
        assert self.core.mixer.get_volume() == 12
        assert self.core.tracklist._next_tlid == 14
        assert self.core.tracklist.get_repeat() is True
        assert self.core.tracklist.get_random() is True
        assert self.core.tracklist.get_consume() is False
        assert self.core.tracklist.get_single() is False
        assert self.core.tracklist.get_length() == 1
        assert self.core.playback._start_paused is True
        assert self.core.playback._start_at_position == 432
        assert self.core.history.get_length() == 2

    def test_delete_state_file_on_restore(self):
        data = models.StoredState(
            version="1",
            state=models.CoreState(
                tracklist=models.TracklistState(
                    repeat=True,
                    random=True,
                    consume=False,
                    single=False,
                    next_tlid=12,
                    tl_tracks=[TlTrack(tlid=12, track=Track(uri="a:a"))],
                ),
                history=models.HistoryState(),
                playback=models.PlaybackState(
                    tlid=12,
                    state="paused",
                    time_position=432,
                ),
                mixer=models.MixerState(),
            ),
        )
        storage.dump(self.state_file, data)
        assert self.state_file.is_file()

        self.core._setup()

        assert not self.state_file.exists()
