from typing import List, Optional
from unittest import mock

import pykka
import pytest

from mopidy.audio import PlaybackState
from mopidy.core import Core as BaseCore
from mopidy.core import PlaybackController as BasePlayback
from mopidy.core import TracklistController as BaseTracklist
from mopidy.models import TlTrack, Track


def generate_tl_track(
    tlid: int, length: Optional[int] = None, bitrate: Optional[int] = None
) -> TlTrack:
    track = Track(
        uri=f"dummy1:/music/track{tlid}.mp3",
        name=f"Track {tlid}",
        length=length,
        bitrate=bitrate,
    )
    return TlTrack(tlid=tlid, track=track)


def generate_tl_tracks(
    amount: int, length: Optional[int] = None, bitrate: Optional[int] = None
) -> List[TlTrack]:
    tl_tracks = []
    for tlid in range(1, amount + 1):
        tl_tracks.append(
            generate_tl_track(tlid, length=length, bitrate=bitrate)
        )
    return tl_tracks


class Core(BaseCore):
    def __init__(self, mixer, playback, tracklist):
        self.mixer = pykka.traversable(mixer)
        self.playback = pykka.traversable(playback)
        self.tracklist = pykka.traversable(tracklist)


class DummyMixer:
    def __init__(self, volume, mute):
        self.volume = volume
        self.mute = mute

    def get_volume(self):
        return self.volume

    def get_mute(self):
        return self.mute


class Playback(BasePlayback):
    def __init__(
        self, state, current_tl_track, time_position, stream_title=None
    ):
        self._state = state
        self._current_tl_track = current_tl_track
        self._time_position = time_position
        self._stream_title = stream_title

    def get_time_position(self):
        return self._time_position


class Tracklist(BaseTracklist):
    def __init__(
        self,
        playback,
        tl_tracks,
        version=1,
        consume=False,
        random=False,
        repeat=False,
        single=False,
    ):
        self.core = mock.Mock()
        self.core.playback = playback

        self._tl_tracks = tl_tracks
        self._version = version
        self._consume = consume
        self._random = random
        self._repeat = repeat
        self._single = single

        if random:
            self._shuffled = list(reversed(tl_tracks))
        else:
            self._shuffled = []

        self._next_tlid = len(tl_tracks) + 1


def teardown_function():
    pykka.ActorRegistry.stop_all()


def test_playing():
    tl_tracks = generate_tl_tracks(3, length=20000, bitrate=320)
    current_tl_track = tl_tracks[1]

    mixer = DummyMixer(60, False)
    playback = Playback(PlaybackState.PLAYING, current_tl_track, 8512)
    tracklist = Tracklist(playback, tl_tracks)
    core = Core(mixer, playback, tracklist)

    status = core.get_status()
    assert status == {
        "playback_state": "playing",
        "playback_time_position": 8,
        "playback_time_position_msec": 8512,
        "playback_time_total": 20,
        "playback_time_total_msec": 20000,
        "playback_bitrate": 320,
        "stream_title": None,
        "volume": 60,
        "mute": False,
        "repeat": False,
        "random": False,
        "single": False,
        "consume": False,
        "tracklist_version": 1,
        "tracklist_length": 3,
        "current_track_index": 1,
        "current_track_tlid": 2,
        "next_track_index": 2,
        "next_track_tlid": 3,
        "previous_track_index": 0,
        "previous_track_tlid": 1,
        "eot_track_index": 2,
        "eot_track_tlid": 3,
    }


def test_playing_tracklist_end():
    tl_tracks = generate_tl_tracks(6, length=289510, bitrate=64)
    current_tl_track = tl_tracks[5]

    mixer = DummyMixer(75, False)
    playback = Playback(PlaybackState.PLAYING, current_tl_track, 168012)
    tracklist = Tracklist(playback, tl_tracks, version=4)
    core = Core(mixer, playback, tracklist)

    status = core.get_status()
    assert status == {
        "playback_state": "playing",
        "playback_time_position": 168,
        "playback_time_position_msec": 168012,
        "playback_time_total": 289,
        "playback_time_total_msec": 289510,
        "playback_bitrate": 64,
        "stream_title": None,
        "volume": 75,
        "mute": False,
        "repeat": False,
        "random": False,
        "single": False,
        "consume": False,
        "tracklist_version": 4,
        "tracklist_length": 6,
        "current_track_index": 5,
        "current_track_tlid": 6,
        "next_track_index": None,
        "next_track_tlid": None,
        "previous_track_index": 4,
        "previous_track_tlid": 5,
        "eot_track_index": None,
        "eot_track_tlid": None,
    }


def test_playing_consume():
    tl_tracks = generate_tl_tracks(4, length=45438, bitrate=128)
    current_tl_track = tl_tracks[2]

    mixer = DummyMixer(88, False)
    playback = Playback(PlaybackState.PLAYING, current_tl_track, 31567)
    tracklist = Tracklist(playback, tl_tracks, version=2, consume=True)
    core = Core(mixer, playback, tracklist)

    status = core.get_status()
    assert status == {
        "playback_state": "playing",
        "playback_time_position": 31,
        "playback_time_position_msec": 31567,
        "playback_time_total": 45,
        "playback_time_total_msec": 45438,
        "playback_bitrate": 128,
        "stream_title": None,
        "volume": 88,
        "mute": False,
        "repeat": False,
        "random": False,
        "single": False,
        "consume": True,
        "tracklist_version": 2,
        "tracklist_length": 4,
        "current_track_index": 2,
        "current_track_tlid": 3,
        "next_track_index": 3,
        "next_track_tlid": 4,
        "previous_track_index": 2,
        "previous_track_tlid": 3,
        "eot_track_index": 3,
        "eot_track_tlid": 4,
    }


def test_playing_repeat():
    tl_tracks = generate_tl_tracks(5, length=39016, bitrate=256)
    current_tl_track = tl_tracks[2]

    mixer = DummyMixer(23, True)
    playback = Playback(PlaybackState.PLAYING, current_tl_track, 35712)
    tracklist = Tracklist(playback, tl_tracks, version=3, repeat=True)
    core = Core(mixer, playback, tracklist)

    status = core.get_status()
    assert status == {
        "playback_state": "playing",
        "playback_time_position": 35,
        "playback_time_position_msec": 35712,
        "playback_time_total": 39,
        "playback_time_total_msec": 39016,
        "playback_bitrate": 256,
        "stream_title": None,
        "volume": 23,
        "mute": True,
        "repeat": True,
        "random": False,
        "single": False,
        "consume": False,
        "tracklist_version": 3,
        "tracklist_length": 5,
        "current_track_index": 2,
        "current_track_tlid": 3,
        "next_track_index": 3,
        "next_track_tlid": 4,
        "previous_track_index": 2,
        "previous_track_tlid": 3,
        "eot_track_index": 3,
        "eot_track_tlid": 4,
    }


def test_playing_single():
    tl_tracks = generate_tl_tracks(2, length=116354, bitrate=160)
    current_tl_track = tl_tracks[0]

    mixer = DummyMixer(99, False)
    playback = Playback(PlaybackState.PLAYING, current_tl_track, 78962)
    tracklist = Tracklist(playback, tl_tracks, single=True)
    core = Core(mixer, playback, tracklist)

    status = core.get_status()
    assert status == {
        "playback_state": "playing",
        "playback_time_position": 78,
        "playback_time_position_msec": 78962,
        "playback_time_total": 116,
        "playback_time_total_msec": 116354,
        "playback_bitrate": 160,
        "stream_title": None,
        "volume": 99,
        "mute": False,
        "repeat": False,
        "random": False,
        "single": True,
        "consume": False,
        "tracklist_version": 1,
        "tracklist_length": 2,
        "current_track_index": 0,
        "current_track_tlid": 1,
        "next_track_index": 1,
        "next_track_tlid": 2,
        "previous_track_index": None,
        "previous_track_tlid": None,
        "eot_track_index": None,
        "eot_track_tlid": None,
    }


def test_playing_single_repeat():
    tl_tracks = generate_tl_tracks(3, length=236588, bitrate=192)
    current_tl_track = tl_tracks[2]

    mixer = DummyMixer(1, False)
    playback = Playback(PlaybackState.PLAYING, current_tl_track, 57922)
    tracklist = Tracklist(playback, tl_tracks, repeat=True, single=True)
    core = Core(mixer, playback, tracklist)

    status = core.get_status()
    assert status == {
        "playback_state": "playing",
        "playback_time_position": 57,
        "playback_time_position_msec": 57922,
        "playback_time_total": 236,
        "playback_time_total_msec": 236588,
        "playback_bitrate": 192,
        "stream_title": None,
        "volume": 1,
        "mute": False,
        "repeat": True,
        "random": False,
        "single": True,
        "consume": False,
        "tracklist_version": 1,
        "tracklist_length": 3,
        "current_track_index": 2,
        "current_track_tlid": 3,
        "next_track_index": 0,
        "next_track_tlid": 1,
        "previous_track_index": 2,
        "previous_track_tlid": 3,
        "eot_track_index": 2,
        "eot_track_tlid": 3,
    }


def test_playing_consume_repeat():
    tl_tracks = generate_tl_tracks(7, length=134323, bitrate=128)
    current_tl_track = tl_tracks[0]

    mixer = DummyMixer(100, True)
    playback = Playback(PlaybackState.PLAYING, current_tl_track, 1670)
    tracklist = Tracklist(
        playback, tl_tracks, version=6, consume=True, repeat=True
    )
    core = Core(mixer, playback, tracklist)

    status = core.get_status()
    assert status == {
        "playback_state": "playing",
        "playback_time_position": 1,
        "playback_time_position_msec": 1670,
        "playback_time_total": 134,
        "playback_time_total_msec": 134323,
        "playback_bitrate": 128,
        "stream_title": None,
        "volume": 100,
        "mute": True,
        "repeat": True,
        "random": False,
        "single": False,
        "consume": True,
        "tracklist_version": 6,
        "tracklist_length": 7,
        "current_track_index": 0,
        "current_track_tlid": 1,
        "next_track_index": 1,
        "next_track_tlid": 2,
        "previous_track_index": 0,
        "previous_track_tlid": 1,
        "eot_track_index": 1,
        "eot_track_tlid": 2,
    }


def test_playing_random():
    tl_tracks = generate_tl_tracks(10, length=36882, bitrate=320)
    current_tl_track = tl_tracks[5]

    mixer = DummyMixer(42, False)
    playback = Playback(PlaybackState.PLAYING, current_tl_track, 22909)
    tracklist = Tracklist(playback, tl_tracks, version=103, random=True)
    core = Core(mixer, playback, tracklist)

    status = core.get_status()
    assert status == {
        "playback_state": "playing",
        "playback_time_position": 22,
        "playback_time_position_msec": 22909,
        "playback_time_total": 36,
        "playback_time_total_msec": 36882,
        "playback_bitrate": 320,
        "stream_title": None,
        "volume": 42,
        "mute": False,
        "repeat": False,
        "random": True,
        "single": False,
        "consume": False,
        "tracklist_version": 103,
        "tracklist_length": 10,
        "current_track_index": 5,
        "current_track_tlid": 6,
        "next_track_index": 9,
        "next_track_tlid": 10,
        "previous_track_index": 5,
        "previous_track_tlid": 6,
        "eot_track_index": 9,
        "eot_track_tlid": 10,
    }


def test_playing_stream():
    tl_tracks = generate_tl_tracks(1, bitrate=96)
    current_tl_track = tl_tracks[0]

    mixer = DummyMixer(90, False)
    playback = Playback(
        PlaybackState.PLAYING,
        current_tl_track,
        543769,
        stream_title="The Radio",
    )
    tracklist = Tracklist(playback, tl_tracks, version=2)
    core = Core(mixer, playback, tracklist)

    status = core.get_status()
    assert status == {
        "playback_state": "playing",
        "playback_time_position": 543,
        "playback_time_position_msec": 543769,
        "playback_time_total": None,
        "playback_time_total_msec": None,
        "playback_bitrate": 96,
        "stream_title": "The Radio",
        "volume": 90,
        "mute": False,
        "repeat": False,
        "random": False,
        "single": False,
        "consume": False,
        "tracklist_version": 2,
        "tracklist_length": 1,
        "current_track_index": 0,
        "current_track_tlid": 1,
        "next_track_index": None,
        "next_track_tlid": None,
        "previous_track_index": None,
        "previous_track_tlid": None,
        "eot_track_index": None,
        "eot_track_tlid": None,
    }


def test_paused():
    tl_tracks = generate_tl_tracks(7, length=65203, bitrate=320)
    current_tl_track = tl_tracks[4]

    mixer = DummyMixer(78, True)
    playback = Playback(PlaybackState.PAUSED, current_tl_track, 7127)
    tracklist = Tracklist(playback, tl_tracks, version=9)
    core = Core(mixer, playback, tracklist)

    status = core.get_status()
    assert status == {
        "playback_state": "paused",
        "playback_time_position": 7,
        "playback_time_position_msec": 7127,
        "playback_time_total": 65,
        "playback_time_total_msec": 65203,
        "playback_bitrate": 320,
        "stream_title": None,
        "volume": 78,
        "mute": True,
        "repeat": False,
        "random": False,
        "single": False,
        "consume": False,
        "tracklist_version": 9,
        "tracklist_length": 7,
        "current_track_index": 4,
        "current_track_tlid": 5,
        "next_track_index": 5,
        "next_track_tlid": 6,
        "previous_track_index": 3,
        "previous_track_tlid": 4,
        "eot_track_index": 5,
        "eot_track_tlid": 6,
    }


def test_stopped():
    tl_tracks = generate_tl_tracks(4, length=154978, bitrate=192)
    current_tl_track = tl_tracks[2]

    mixer = DummyMixer(24, False)
    playback = Playback(PlaybackState.STOPPED, current_tl_track, 97003)
    tracklist = Tracklist(playback, tl_tracks, version=23)
    core = Core(mixer, playback, tracklist)

    status = core.get_status()
    assert status == {
        "playback_state": "stopped",
        "playback_time_position": 97,
        "playback_time_position_msec": 97003,
        "playback_time_total": 154,
        "playback_time_total_msec": 154978,
        "playback_bitrate": 192,
        "stream_title": None,
        "volume": 24,
        "mute": False,
        "repeat": False,
        "random": False,
        "single": False,
        "consume": False,
        "tracklist_version": 23,
        "tracklist_length": 4,
        "current_track_index": 2,
        "current_track_tlid": 3,
        "next_track_index": 3,
        "next_track_tlid": 4,
        "previous_track_index": 1,
        "previous_track_tlid": 2,
        "eot_track_index": 3,
        "eot_track_tlid": 4,
    }


def test_stopped_not_played_yet():
    tl_tracks = generate_tl_tracks(6, length=345122, bitrate=32)

    mixer = DummyMixer(44, False)
    playback = Playback(PlaybackState.STOPPED, None, None)
    tracklist = Tracklist(playback, tl_tracks, version=3)
    core = Core(mixer, playback, tracklist)

    status = core.get_status()
    assert status == {
        "playback_state": "stopped",
        "playback_time_position": None,
        "playback_time_position_msec": None,
        "playback_time_total": None,
        "playback_time_total_msec": None,
        "playback_bitrate": None,
        "stream_title": None,
        "volume": 44,
        "mute": False,
        "repeat": False,
        "random": False,
        "single": False,
        "consume": False,
        "tracklist_version": 3,
        "tracklist_length": 6,
        "current_track_index": None,
        "current_track_tlid": None,
        "next_track_index": 0,
        "next_track_tlid": 1,
        "previous_track_index": None,
        "previous_track_tlid": None,
        "eot_track_index": 0,
        "eot_track_tlid": 1,
    }


@pytest.mark.parametrize("consume", (True, False))
@pytest.mark.parametrize("random", (True, False))
@pytest.mark.parametrize("repeat", (True, False))
@pytest.mark.parametrize("single", (True, False))
def test_empty_tracklist(
    consume: bool, random: bool, repeat: bool, single: bool
):
    mixer = DummyMixer(36, False)
    playback = Playback(PlaybackState.STOPPED, None, None)
    tracklist = Tracklist(
        playback,
        [],
        consume=consume,
        random=random,
        repeat=repeat,
        single=single,
    )
    core = Core(mixer, playback, tracklist)

    status = core.get_status()
    assert status == {
        "playback_state": "stopped",
        "playback_time_position": None,
        "playback_time_position_msec": None,
        "playback_time_total": None,
        "playback_time_total_msec": None,
        "playback_bitrate": None,
        "stream_title": None,
        "volume": 36,
        "mute": False,
        "repeat": repeat,
        "random": random,
        "single": single,
        "consume": consume,
        "tracklist_version": 1,
        "tracklist_length": 0,
        "current_track_index": None,
        "current_track_tlid": None,
        "next_track_index": None,
        "next_track_tlid": None,
        "previous_track_index": None,
        "previous_track_tlid": None,
        "eot_track_index": None,
        "eot_track_tlid": None,
    }
