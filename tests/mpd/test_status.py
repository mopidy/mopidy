import unittest

import pykka

from mopidy import core
from mopidy.core import PlaybackState
from mopidy.internal import deprecation
from mopidy.models import Track
from mopidy.mpd import dispatcher
from mopidy.mpd.protocol import status

from tests import dummy_audio, dummy_backend, dummy_mixer

PAUSED = PlaybackState.PAUSED
PLAYING = PlaybackState.PLAYING
STOPPED = PlaybackState.STOPPED

# FIXME migrate to using protocol.BaseTestCase instead of status.stats
# directly?


class StatusHandlerTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        config = {"core": {"max_tracklist_length": 10000}}

        self.audio = dummy_audio.create_proxy()
        self.mixer = dummy_mixer.create_proxy()
        self.backend = dummy_backend.create_proxy(audio=self.audio)

        with deprecation.ignore():
            self.core = core.Core.start(
                config,
                audio=self.audio,
                mixer=self.mixer,
                backends=[self.backend],
            ).proxy()

        self.dispatcher = dispatcher.MpdDispatcher(core=self.core)
        self.context = self.dispatcher.context

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()

    def set_tracklist(self, tracks):
        self.backend.library.dummy_library = tracks
        self.core.tracklist.add(uris=[track.uri for track in tracks]).get()

    def test_stats_method(self):
        result = status.stats(self.context)
        assert "artists" in result
        assert int(result["artists"]) >= 0
        assert "albums" in result
        assert int(result["albums"]) >= 0
        assert "songs" in result
        assert int(result["songs"]) >= 0
        assert "uptime" in result
        assert int(result["uptime"]) >= 0
        assert "db_playtime" in result
        assert int(result["db_playtime"]) >= 0
        assert "db_update" in result
        assert int(result["db_update"]) >= 0
        assert "playtime" in result
        assert int(result["playtime"]) >= 0

    def test_status_method_contains_volume_with_na_value(self):
        result = dict(status.status(self.context))
        assert "volume" in result
        assert int(result["volume"]) == (-1)

    def test_status_method_contains_volume(self):
        self.core.mixer.set_volume(17)
        result = dict(status.status(self.context))
        assert "volume" in result
        assert int(result["volume"]) == 17

    def test_status_method_contains_repeat_is_0(self):
        result = dict(status.status(self.context))
        assert "repeat" in result
        assert int(result["repeat"]) == 0

    def test_status_method_contains_repeat_is_1(self):
        self.core.tracklist.set_repeat(True)
        result = dict(status.status(self.context))
        assert "repeat" in result
        assert int(result["repeat"]) == 1

    def test_status_method_contains_random_is_0(self):
        result = dict(status.status(self.context))
        assert "random" in result
        assert int(result["random"]) == 0

    def test_status_method_contains_random_is_1(self):
        self.core.tracklist.set_random(True)
        result = dict(status.status(self.context))
        assert "random" in result
        assert int(result["random"]) == 1

    def test_status_method_contains_single(self):
        result = dict(status.status(self.context))
        assert "single" in result
        assert int(result["single"]) in (0, 1)

    def test_status_method_contains_consume_is_0(self):
        result = dict(status.status(self.context))
        assert "consume" in result
        assert int(result["consume"]) == 0

    def test_status_method_contains_consume_is_1(self):
        self.core.tracklist.set_consume(True)
        result = dict(status.status(self.context))
        assert "consume" in result
        assert int(result["consume"]) == 1

    def test_status_method_contains_playlist(self):
        result = dict(status.status(self.context))
        assert "playlist" in result
        assert int(result["playlist"]) >= 0
        assert int(result["playlist"]) <= ((2 ** 31) - 1)

    def test_status_method_contains_playlistlength(self):
        result = dict(status.status(self.context))
        assert "playlistlength" in result
        assert int(result["playlistlength"]) >= 0

    def test_status_method_contains_xfade(self):
        result = dict(status.status(self.context))
        assert "xfade" in result
        assert int(result["xfade"]) >= 0

    def test_status_method_contains_state_is_play(self):
        self.core.playback.set_state(PLAYING)
        result = dict(status.status(self.context))
        assert "state" in result
        assert result["state"] == "play"

    def test_status_method_contains_state_is_stop(self):
        self.core.playback.set_state(STOPPED)
        result = dict(status.status(self.context))
        assert "state" in result
        assert result["state"] == "stop"

    def test_status_method_contains_state_is_pause(self):
        self.core.playback.set_state(PLAYING)
        self.core.playback.set_state(PAUSED)
        result = dict(status.status(self.context))
        assert "state" in result
        assert result["state"] == "pause"

    def test_status_method_when_playlist_loaded_contains_song(self):
        self.set_tracklist([Track(uri="dummy:/a")])
        self.core.playback.play().get()
        result = dict(status.status(self.context))
        assert "song" in result
        assert int(result["song"]) >= 0

    def test_status_method_when_playlist_loaded_contains_tlid_as_songid(self):
        self.set_tracklist([Track(uri="dummy:/a")])
        self.core.playback.play().get()
        result = dict(status.status(self.context))
        assert "songid" in result
        assert int(result["songid"]) == 1

    def test_status_method_when_playlist_loaded_contains_nextsong(self):
        self.set_tracklist([Track(uri="dummy:/a"), Track(uri="dummy:/b")])
        self.core.playback.play().get()
        result = dict(status.status(self.context))
        assert "nextsong" in result
        assert int(result["nextsong"]) >= 0

    def test_status_method_when_playlist_loaded_contains_nextsongid(self):
        self.set_tracklist([Track(uri="dummy:/a"), Track(uri="dummy:/b")])
        self.core.playback.play().get()
        result = dict(status.status(self.context))
        assert "nextsongid" in result
        assert int(result["nextsongid"]) == 2

    def test_status_method_when_playing_contains_time_with_no_length(self):
        self.set_tracklist([Track(uri="dummy:/a", length=None)])
        self.core.playback.play().get()
        result = dict(status.status(self.context))
        assert "time" in result
        (position, total) = result["time"].split(":")
        position = int(position)
        total = int(total)
        assert position <= total

    def test_status_method_when_playing_contains_time_with_length(self):
        self.set_tracklist([Track(uri="dummy:/a", length=10000)])
        self.core.playback.play().get()
        result = dict(status.status(self.context))
        assert "time" in result
        (position, total) = result["time"].split(":")
        position = int(position)
        total = int(total)
        assert position <= total

    def test_status_method_when_playing_contains_elapsed(self):
        self.set_tracklist([Track(uri="dummy:/a", length=60000)])
        self.core.playback.play().get()
        self.core.playback.pause()
        self.core.playback.seek(59123)
        result = dict(status.status(self.context))
        assert "elapsed" in result
        assert result["elapsed"] == "59.123"

    def test_status_method_when_starting_playing_contains_elapsed_zero(self):
        self.set_tracklist([Track(uri="dummy:/a", length=10000)])
        self.core.playback.play().get()
        self.core.playback.pause()
        result = dict(status.status(self.context))
        assert "elapsed" in result
        assert result["elapsed"] == "0.000"

    def test_status_method_when_playing_contains_bitrate(self):
        self.set_tracklist([Track(uri="dummy:/a", bitrate=3200)])
        self.core.playback.play().get()
        result = dict(status.status(self.context))
        assert "bitrate" in result
        assert int(result["bitrate"]) == 3200
