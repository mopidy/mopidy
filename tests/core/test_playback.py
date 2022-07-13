from unittest import mock

import pykka
import pytest

from mopidy import backend, core
from mopidy.internal import deprecation
from mopidy.internal.models import PlaybackState
from mopidy.models import Track

from tests import dummy_audio, dummy_backend


class MyTestPlaybackProvider(backend.PlaybackProvider):
    def __init__(self, audio, backend):
        super().__init__(audio, backend)
        self._call_limit = 10
        self._call_count = 0
        self._call_onetime = False

    def reset_call_limit(self):
        self._call_count = 0
        self._call_onetime = False

    def is_call_limit_reached(self):
        return self._call_count > self._call_limit

    def _translate_uri_call_limit(self, uri):
        self._call_count += 1
        if self._call_count > self._call_limit:
            # return any url (not 'None') to stop the endless loop
            return "assert: call limit reached"
        if "limit_never" in uri:
            # unplayable
            return None
        elif "limit_one" in uri:
            # one time playable
            if self._call_onetime:
                return None
            self._call_onetime = True
        return uri

    def translate_uri(self, uri):
        if "error" in uri:
            raise Exception(uri)
        elif "unplayable" in uri:
            return None
        elif "limit" in uri:
            return self._translate_uri_call_limit(uri)
        else:
            return uri


class MyTestBackend(dummy_backend.DummyBackend):
    def __init__(self, config, audio):
        super().__init__(config, audio)
        self.playback = MyTestPlaybackProvider(audio=audio, backend=self)


class BaseTest:
    config = {"core": {"max_tracklist_length": 10000}}
    tracks = [
        Track(uri="dummy:a", length=1234, name="foo"),
        Track(uri="dummy:b", length=1234),
        Track(uri="dummy:c", length=1234),
    ]

    def setup_method(self, method):
        self.audio = dummy_audio.create_proxy(config=self.config, mixer=None)
        self.backend = MyTestBackend.start(
            audio=self.audio, config=self.config
        ).proxy()
        self.core = core.Core(
            audio=self.audio, backends=[self.backend], config=self.config
        )
        self.playback = self.core.playback

        # We don't have a core actor running, so call about to finish directly.
        self.audio.set_about_to_finish_callback(
            self.playback._on_about_to_finish
        )

        with deprecation.ignore():
            self.core.tracklist.add(self.tracks)

        self.events = []
        self.patcher = mock.patch("mopidy.audio.listener.AudioListener.send")
        self.send_mock = self.patcher.start()

        def send(event, **kwargs):
            self.events.append((event, kwargs))

        self.send_mock.side_effect = send

    def teardown_method(self):
        pykka.ActorRegistry.stop_all()
        self.patcher.stop()

    def replay_events(self, until=None):
        while self.events:
            if self.events[0][0] == until:
                break
            event, kwargs = self.events.pop(0)
            self.core.on_event(event, **kwargs)

    def trigger_about_to_finish(self, replay_until=None):
        self.replay_events()
        callback = self.audio.get_about_to_finish_callback().get()
        callback()
        self.replay_events(until=replay_until)


class TestPlayHandling(BaseTest):
    def test_get_current_tl_track_play(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()

        assert self.core.playback.get_current_tl_track() == tl_tracks[0]

    def test_get_current_track_play(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()

        assert self.core.playback.get_current_track() == self.tracks[0]

    def test_get_current_tlid_play(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()

        assert self.core.playback.get_current_tlid() == tl_tracks[0].tlid

    def test_play_skips_to_next_on_unplayable_track(self):
        """Checks that we handle backend.change_track failing."""
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.audio.trigger_fake_playback_failure(tl_tracks[0].track.uri)

        self.core.playback.play(tl_tracks[0])
        self.replay_events()

        current_tl_track = self.core.playback.get_current_tl_track()
        assert tl_tracks[1] == current_tl_track

    def test_resume_skips_to_next_on_unplayable_track(self):
        """Checks that we handle backend.change_track failing when
        resuming playback."""
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.core.playback.pause()

        self.audio.trigger_fake_playback_failure(tl_tracks[1].track.uri)

        self.core.playback.next()
        self.core.playback.resume()
        self.replay_events()

        current_tl_track = self.core.playback.get_current_tl_track()
        assert tl_tracks[2] == current_tl_track

    def test_play_tlid(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tlid=tl_tracks[1].tlid)
        self.replay_events()

        current_tl_track = self.core.playback.get_current_tl_track()
        assert tl_tracks[1] == current_tl_track

    def test_default_is_live_behaviour_is_not_live(self):
        assert not self.backend.playback.is_live(self.tracks[0].uri).get()

    def test_download_buffering_is_not_enabled_by_default(self):
        assert not self.backend.playback.should_download(
            self.tracks[0].uri
        ).get()


class TestNextHandling(BaseTest):
    def test_get_current_tl_track_next(self):
        self.core.playback.play()
        self.replay_events()

        self.core.playback.next()
        self.replay_events()

        tl_tracks = self.core.tracklist.get_tl_tracks()
        current_tl_track = self.core.playback.get_current_tl_track()
        assert current_tl_track == tl_tracks[1]

    def test_get_pending_tl_track_next(self):
        self.core.playback.play()
        self.replay_events()

        self.core.playback.next()

        tl_tracks = self.core.tracklist.get_tl_tracks()
        assert self.core.playback._pending_tl_track == tl_tracks[1]

    def test_get_current_track_next(self):
        self.core.playback.play()
        self.replay_events()

        self.core.playback.next()
        self.replay_events()

        current_track = self.core.playback.get_current_track()
        assert current_track == self.tracks[1]

    @pytest.mark.parametrize(
        "repeat, random, single, consume, index, result",
        [
            (False, False, False, False, 0, 1),
            (False, False, False, False, 2, None),
            (True, False, False, False, 0, 1),
            (True, False, False, False, 2, 0),
        ],
    )
    def test_next_all_modes(
        self, repeat, random, single, consume, index, result
    ):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[index])
        self.replay_events()
        self.core.tracklist.set_repeat(repeat)
        self.core.tracklist.set_random(random)
        self.core.tracklist.set_single(single)
        self.core.tracklist.set_consume(consume)

        self.core.playback.next()
        self.replay_events()

        if result is None:
            assert self.core.playback.get_current_tl_track() is None
        else:
            assert (
                self.core.playback.get_current_tl_track() == tl_tracks[result]
            )

    def test_next_keeps_finished_track_in_tracklist(self):
        tl_track = self.core.tracklist.get_tl_tracks()[0]

        self.core.playback.play(tl_track)
        self.replay_events()

        self.core.playback.next()
        self.replay_events()

        assert tl_track in self.core.tracklist.get_tl_tracks()

    def test_next_skips_over_unplayable_track(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()
        self.audio.trigger_fake_playback_failure(tl_tracks[1].track.uri)
        self.core.playback.play(tl_tracks[0])
        self.replay_events()

        self.core.playback.next()
        self.replay_events()

        assert self.core.playback.get_current_tl_track() == tl_tracks[2]

    def test_next_skips_over_change_track_error(self):
        # Trigger an exception in translate_uri.
        track = Track(uri="dummy:error", length=1234)
        with deprecation.ignore():
            self.core.tracklist.add(tracks=[track], at_position=1)

        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play()
        self.replay_events()

        self.core.playback.next()
        self.replay_events()

        assert self.core.playback.get_current_tl_track() == tl_tracks[2]

    def test_next_skips_over_change_track_unplayable(self):
        # Make translate_uri return None.
        track = Track(uri="dummy:unplayable", length=1234)
        with deprecation.ignore():
            self.core.tracklist.add(tracks=[track], at_position=1)

        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play()
        self.replay_events()

        self.core.playback.next()
        self.replay_events()

        assert self.core.playback.get_current_tl_track() == tl_tracks[2]


class TestPreviousHandling(BaseTest):
    def test_get_current_tl_track_prev(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[1])
        self.core.playback.previous()
        self.replay_events()

        assert self.core.playback.get_current_tl_track() == tl_tracks[0]

    def test_get_current_track_prev(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[1])
        self.core.playback.previous()
        self.replay_events()

        assert self.core.playback.get_current_track() == self.tracks[0]

    @pytest.mark.parametrize(
        "repeat, random, single, consume, index, result",
        [
            (False, False, False, False, 0, None),
            (False, False, False, False, 1, 0),
            (True, False, False, False, 0, 0),  # FIXME: #1694
            (True, False, False, False, 1, 1),  # FIXME: #1694
        ],
    )
    def test_previous_all_modes(
        self, repeat, random, single, consume, index, result
    ):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[index])
        self.core.tracklist.set_repeat(repeat)
        self.core.tracklist.set_random(random)
        self.core.tracklist.set_single(single)
        self.core.tracklist.set_consume(consume)

        self.core.playback.previous()
        self.replay_events()

        if result is None:
            assert self.core.playback.get_current_tl_track() is None
        else:
            assert (
                self.core.playback.get_current_tl_track() == tl_tracks[result]
            )

    def test_previous_keeps_finished_track_in_tracklist(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[1])

        self.core.playback.previous()
        self.replay_events()

        assert tl_tracks[1] in self.core.tracklist.get_tl_tracks()

    def test_previous_keeps_finished_track_even_in_consume_mode(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[1])
        self.core.tracklist.set_consume(True)

        self.core.playback.previous()
        self.replay_events()

        assert tl_tracks[1] in self.core.tracklist.get_tl_tracks()

    def test_previous_skips_over_unplayable_track(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()
        self.audio.trigger_fake_playback_failure(tl_tracks[1].track.uri)
        self.core.playback.play(tl_tracks[2])
        self.replay_events()

        self.core.playback.previous()
        self.replay_events()

        assert self.core.playback.get_current_tl_track() == tl_tracks[0]

    def test_previous_skips_over_change_track_error(self):
        # Trigger an exception in translate_uri.
        track = Track(uri="dummy:error", length=1234)
        with deprecation.ignore():
            self.core.tracklist.add(tracks=[track], at_position=1)

        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[2])
        self.replay_events()

        self.core.playback.previous()
        self.replay_events()

        assert self.core.playback.get_current_tl_track() == tl_tracks[0]

    def test_previous_skips_over_change_track_unplayable(self):
        # Makes translate_uri return None.
        track = Track(uri="dummy:unplayable", length=1234)
        with deprecation.ignore():
            self.core.tracklist.add(tracks=[track], at_position=1)

        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[2])
        self.replay_events()

        self.core.playback.previous()
        self.replay_events()

        assert self.core.playback.get_current_tl_track() == tl_tracks[0]


class TestOnAboutToFinish(BaseTest):
    def test_on_about_to_finish_keeps_finished_track_in_tracklist(self):
        tl_track = self.core.tracklist.get_tl_tracks()[0]

        self.core.playback.play(tl_track)
        self.trigger_about_to_finish()

        assert tl_track in self.core.tracklist.get_tl_tracks()

    def test_on_about_to_finish_skips_over_change_track_error(self):
        # Trigger an exception in translate_uri.
        track = Track(uri="dummy:error", length=1234)
        with deprecation.ignore():
            self.core.tracklist.add(tracks=[track], at_position=1)

        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()

        self.trigger_about_to_finish()

        assert self.core.playback.get_current_tl_track() == tl_tracks[2]

    def test_on_about_to_finish_skips_over_change_track_unplayable(self):
        # Makes translate_uri return None.
        track = Track(uri="dummy:unplayable", length=1234)
        with deprecation.ignore():
            self.core.tracklist.add(tracks=[track], at_position=1)

        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()

        self.trigger_about_to_finish()

        assert self.core.playback.get_current_tl_track() == tl_tracks[2]


class TestConsumeHandling(BaseTest):
    def test_next_in_consume_mode_removes_finished_track(self):
        tl_track = self.core.tracklist.get_tl_tracks()[0]

        self.core.playback.play(tl_track)
        self.core.tracklist.set_consume(True)
        self.replay_events()

        self.core.playback.next()
        self.replay_events()

        assert tl_track not in self.core.tracklist.get_tl_tracks()

    def test_next_in_consume_mode_removes_unplayable_track(self):
        last_playable_tl_track = self.core.tracklist.get_tl_tracks()[-2]
        unplayable_tl_track = self.core.tracklist.get_tl_tracks()[-1]
        self.audio.trigger_fake_playback_failure(unplayable_tl_track.track.uri)

        self.core.playback.play(last_playable_tl_track)
        self.core.tracklist.set_consume(True)

        self.core.playback.next()
        self.replay_events()

        assert unplayable_tl_track not in self.core.tracklist.get_tl_tracks()

    def test_on_about_to_finish_in_consume_mode_removes_finished_track(self):
        tl_track = self.core.tracklist.get_tl_tracks()[0]

        self.core.playback.play(tl_track)
        self.core.tracklist.set_consume(True)
        self.trigger_about_to_finish()

        assert tl_track not in self.core.tracklist.get_tl_tracks()

    def test_next_in_consume_and_repeat_mode_returns_none_on_last_track(self):
        self.core.playback.play()
        self.core.tracklist.set_consume(True)
        self.core.tracklist.set_repeat(True)
        self.replay_events()

        for _tl_track in self.core.tracklist.get_tl_tracks():
            self.core.playback.next()
            self.replay_events()

        self.core.playback.next()
        self.replay_events()

        assert self.playback.get_state() == "stopped"


class TestCurrentAndPendingTlTrack(BaseTest):
    def test_get_current_tl_track_none(self):
        assert self.core.playback.get_current_tl_track() is None

    def test_get_current_tlid_none(self):
        assert self.core.playback.get_current_tlid() is None

    def test_pending_tl_track_is_none(self):
        self.core.playback.play()
        self.replay_events()
        assert self.playback._pending_tl_track is None

    def test_pending_tl_track_after_about_to_finish(self):
        self.core.playback.play()
        self.replay_events()

        self.trigger_about_to_finish(replay_until="stream_changed")
        assert self.playback._pending_tl_track.track.uri == "dummy:b"

    def test_pending_tl_track_after_stream_changed(self):
        self.trigger_about_to_finish()
        assert self.playback._pending_tl_track is None

    def test_current_tl_track_after_about_to_finish(self):
        self.core.playback.play()
        self.replay_events()
        self.trigger_about_to_finish(replay_until="stream_changed")
        assert self.playback.get_current_track().uri == "dummy:a"

    def test_current_tl_track_after_stream_changed(self):
        self.core.playback.play()
        self.replay_events()
        self.trigger_about_to_finish()
        assert self.playback.get_current_track().uri == "dummy:b"

    def test_current_tl_track_after_end_of_stream(self):
        self.core.playback.play()
        self.replay_events()
        self.trigger_about_to_finish()
        self.trigger_about_to_finish()
        self.trigger_about_to_finish()  # EOS
        assert self.playback.get_current_tl_track() is None


@mock.patch(
    "mopidy.core.playback.listener.CoreListener", spec=core.CoreListener
)
class TestEventEmission(BaseTest):

    maxDiff = None  # noqa: N815

    def test_play_when_stopped_emits_events(self, listener_mock):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()

        assert listener_mock.send.mock_calls == [
            mock.call(
                "playback_state_changed",
                old_state="stopped",
                new_state="playing",
            ),
            mock.call("track_playback_started", tl_track=tl_tracks[0]),
        ]

    def test_play_when_paused_emits_events(self, listener_mock):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()

        self.core.playback.pause()
        self.replay_events()
        listener_mock.reset_mock()

        self.core.playback.play(tl_tracks[1])
        self.replay_events()

        assert listener_mock.send.mock_calls == [
            mock.call(
                "track_playback_ended",
                tl_track=tl_tracks[0],
                time_position=mock.ANY,
            ),
            mock.call(
                "playback_state_changed",
                old_state="paused",
                new_state="playing",
            ),
            mock.call("track_playback_started", tl_track=tl_tracks[1]),
        ]

    def test_play_when_playing_emits_events(self, listener_mock):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()
        listener_mock.reset_mock()

        self.core.playback.play(tl_tracks[2])
        self.replay_events()

        assert listener_mock.send.mock_calls == [
            mock.call(
                "track_playback_ended",
                tl_track=tl_tracks[0],
                time_position=mock.ANY,
            ),
            mock.call(
                "playback_state_changed",
                old_state="playing",
                new_state="playing",
            ),
            mock.call("track_playback_started", tl_track=tl_tracks[2]),
        ]

    def test_pause_emits_events(self, listener_mock):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()

        self.core.playback.seek(1000)
        listener_mock.reset_mock()

        self.core.playback.pause()

        assert listener_mock.send.mock_calls == [
            mock.call(
                "playback_state_changed",
                old_state="playing",
                new_state="paused",
            ),
            mock.call(
                "track_playback_paused",
                tl_track=tl_tracks[0],
                time_position=1000,
            ),
        ]

    def test_resume_emits_events(self, listener_mock):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()

        self.core.playback.pause()
        self.core.playback.seek(1000)
        listener_mock.reset_mock()

        self.core.playback.resume()

        assert listener_mock.send.mock_calls == [
            mock.call(
                "playback_state_changed",
                old_state="paused",
                new_state="playing",
            ),
            mock.call(
                "track_playback_resumed",
                tl_track=tl_tracks[0],
                time_position=1000,
            ),
        ]

    def test_stop_emits_events(self, listener_mock):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()
        self.core.playback.seek(1000)
        self.replay_events()
        listener_mock.reset_mock()

        self.core.playback.stop()
        self.replay_events()

        assert listener_mock.send.mock_calls == [
            mock.call(
                "playback_state_changed",
                old_state="playing",
                new_state="stopped",
            ),
            mock.call(
                "track_playback_ended",
                tl_track=tl_tracks[0],
                time_position=1000,
            ),
        ]

    def test_next_emits_events(self, listener_mock):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()
        self.core.playback.seek(1000)
        self.replay_events()
        listener_mock.reset_mock()

        self.core.playback.next()
        self.replay_events()

        assert listener_mock.send.mock_calls == [
            mock.call(
                "track_playback_ended",
                tl_track=tl_tracks[0],
                time_position=mock.ANY,
            ),
            mock.call(
                "playback_state_changed",
                old_state="playing",
                new_state="playing",
            ),
            mock.call("track_playback_started", tl_track=tl_tracks[1]),
        ]

    def test_next_emits_events_when_consume_mode_is_enabled(
        self, listener_mock
    ):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.tracklist.set_consume(True)
        self.core.playback.play(tl_tracks[0])
        self.replay_events()
        self.core.playback.seek(1000)
        self.replay_events()
        listener_mock.reset_mock()

        self.core.playback.next()
        self.replay_events()

        assert listener_mock.send.mock_calls == [
            mock.call("tracklist_changed"),
            mock.call(
                "track_playback_ended",
                tl_track=tl_tracks[0],
                time_position=mock.ANY,
            ),
            mock.call(
                "playback_state_changed",
                old_state="playing",
                new_state="playing",
            ),
            mock.call("track_playback_started", tl_track=tl_tracks[1]),
        ]

    def test_gapless_track_change_emits_events(self, listener_mock):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()
        listener_mock.reset_mock()

        self.trigger_about_to_finish()

        assert listener_mock.send.mock_calls == [
            mock.call(
                "track_playback_ended",
                tl_track=tl_tracks[0],
                time_position=mock.ANY,
            ),
            mock.call(
                "playback_state_changed",
                old_state="playing",
                new_state="playing",
            ),
            mock.call("track_playback_started", tl_track=tl_tracks[1]),
        ]

    def test_seek_emits_seeked_event(self, listener_mock):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()
        listener_mock.reset_mock()

        self.core.playback.seek(1000)
        self.replay_events()

        listener_mock.send.assert_called_once_with("seeked", time_position=1000)

    def test_seek_past_end_of_track_emits_events(self, listener_mock):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()
        listener_mock.reset_mock()

        self.core.playback.seek(self.tracks[0].length * 5)
        self.replay_events()

        assert listener_mock.send.mock_calls == [
            mock.call(
                "track_playback_ended",
                tl_track=tl_tracks[0],
                time_position=mock.ANY,
            ),
            mock.call(
                "playback_state_changed",
                old_state="playing",
                new_state="playing",
            ),
            mock.call("track_playback_started", tl_track=tl_tracks[1]),
        ]

    def test_seek_race_condition_emits_events(self, listener_mock):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.trigger_about_to_finish(replay_until="stream_changed")
        self.replay_events()
        listener_mock.reset_mock()

        self.core.playback.seek(1000)
        self.replay_events()

        # When we trigger seek after an about to finish the other code that
        # emits track stopped/started and playback_state_changed events gets
        # triggered as we have to switch back to the previous track.
        # The correct behavior would be to only emit seeked.
        assert listener_mock.send.mock_calls == [
            mock.call("seeked", time_position=1000)
        ]

    def test_previous_emits_events(self, listener_mock):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[1])
        self.replay_events()
        listener_mock.reset_mock()

        self.core.playback.previous()
        self.replay_events()

        assert listener_mock.send.mock_calls == [
            mock.call(
                "track_playback_ended",
                tl_track=tl_tracks[1],
                time_position=mock.ANY,
            ),
            mock.call(
                "playback_state_changed",
                old_state="playing",
                new_state="playing",
            ),
            mock.call("track_playback_started", tl_track=tl_tracks[0]),
        ]


class TestUnplayableURI(BaseTest):

    tracks = [
        Track(uri="unplayable://"),
        Track(uri="dummy:b"),
    ]

    def setup_method(self, method):
        super().setup_method(method)
        tl_tracks = self.core.tracklist.get_tl_tracks()
        self.core.playback._set_current_tl_track(tl_tracks[0])

    def test_play_skips_to_next_if_track_is_unplayable(self):
        self.core.playback.play()

        self.replay_events()

        current_track = self.core.playback.get_current_track()
        assert current_track == self.tracks[1]

    def test_pause_changes_state_even_if_track_is_unplayable(self):
        self.core.playback.pause()
        assert self.core.playback.get_state() == core.PlaybackState.PAUSED

    def test_resume_does_nothing_if_track_is_unplayable(self):
        self.core.playback.set_state(core.PlaybackState.PAUSED)
        self.core.playback.resume()

        assert self.core.playback.get_state() == core.PlaybackState.PAUSED

    def test_stop_changes_state_even_if_track_is_unplayable(self):
        self.core.playback.set_state(core.PlaybackState.PAUSED)
        self.core.playback.stop()

        assert self.core.playback.get_state() == core.PlaybackState.STOPPED

    def test_time_position_returns_0_if_track_is_unplayable(self):
        result = self.core.playback.get_time_position()

        assert result == 0

    def test_seek_fails_for_unplayable_track(self):
        self.core.playback.set_state(core.PlaybackState.PLAYING)
        success = self.core.playback.seek(1000)

        assert not success


class TestSeek(BaseTest):
    def test_seek_normalizes_negative_positions_to_zero(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()

        self.core.playback.seek(-100)  # Dummy audio doesn't progress time.
        assert 0 == self.core.playback.get_time_position()

    def test_seek_fails_for_track_without_duration(self):
        track = self.tracks[0].replace(length=None)
        self.core.tracklist.clear()
        with deprecation.ignore():
            self.core.tracklist.add(tracks=[track])

        self.core.playback.play()
        self.replay_events()

        assert not self.core.playback.seek(1000)
        assert 0 == self.core.playback.get_time_position()

    def test_seek_play_stay_playing(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()

        self.core.playback.seek(1000)
        assert self.core.playback.get_state() == core.PlaybackState.PLAYING

    def test_seek_paused_stay_paused(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()

        self.core.playback.pause()
        self.replay_events()

        self.core.playback.seek(1000)
        assert self.core.playback.get_state() == core.PlaybackState.PAUSED

    def test_seek_race_condition_after_about_to_finish(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[0])
        self.replay_events()

        self.trigger_about_to_finish(replay_until="stream_changed")
        self.core.playback.seek(1000)
        self.replay_events()

        current_tl_track = self.core.playback.get_current_tl_track()
        assert current_tl_track == tl_tracks[0]

    def test_seek_stopped_goes_playing(self):
        self.core.playback.stop()
        self.replay_events()

        self.core.playback.seek(1000)
        self.replay_events()
        assert self.core.playback.get_state() == core.PlaybackState.PLAYING


class TestStream(BaseTest):
    def test_get_stream_title_before_playback(self):
        assert self.playback.get_stream_title() is None

    def test_get_stream_title_during_playback(self):
        self.core.playback.play()
        self.replay_events()

        assert self.playback.get_stream_title() is None

    def test_get_stream_title_during_playback_with_tags_change(self):
        self.core.playback.play()
        self.audio.trigger_fake_tags_changed({"title": ["foobar"]}).get()
        self.replay_events()

        assert self.playback.get_stream_title() == "foobar"

    def test_get_stream_title_during_playback_with_tags_unchanged(self):
        self.core.playback.play()
        self.audio.trigger_fake_tags_changed({"title": ["foo"]}).get()
        self.replay_events()

        assert self.playback.get_stream_title() is None

    def test_get_stream_title_after_next(self):
        self.core.playback.play()
        self.audio.trigger_fake_tags_changed({"title": ["foobar"]}).get()
        self.replay_events()

        self.core.playback.next()
        self.replay_events()

        assert self.playback.get_stream_title() is None

    def test_get_stream_title_after_next_with_tags_change(self):
        self.core.playback.play()
        self.audio.trigger_fake_tags_changed({"title": ["foo"]}).get()
        self.replay_events()

        self.core.playback.next()
        self.audio.trigger_fake_tags_changed({"title": ["bar"]}).get()
        self.replay_events()

        assert self.playback.get_stream_title() == "bar"

    def test_get_stream_title_after_stop(self):
        self.core.playback.play()
        self.audio.trigger_fake_tags_changed({"title": ["foobar"]}).get()
        self.replay_events()

        self.core.playback.stop()
        self.replay_events()
        assert self.playback.get_stream_title() is None


class TestBug1871Regression(BaseTest):
    def test(self):
        track = Track(uri="dummy:d", length=1234, name="baz")
        with deprecation.ignore():
            self.core.tracklist.add(tracks=[track], at_position=1)

        self.core.playback.play()
        self.replay_events()

        self.trigger_about_to_finish(replay_until="stream_changed")
        self.audio.trigger_fake_tags_changed({"title": ["foo"]}).get()
        self.replay_events()

        self.audio.trigger_fake_tags_changed({"title": ["baz"]}).get()
        self.replay_events()

        assert self.playback.get_current_track().uri == "dummy:d"
        assert self.playback.get_stream_title() is None


class TestBackendSelection:
    def setup_method(self, method):
        config = {"core": {"max_tracklist_length": 10000}}

        self.backend1 = mock.Mock()
        self.backend1.uri_schemes.get.return_value = ["dummy1"]
        self.playback1 = mock.Mock(spec=backend.PlaybackProvider)
        self.backend1.playback = self.playback1

        self.backend2 = mock.Mock()
        self.backend2.uri_schemes.get.return_value = ["dummy2"]
        self.playback2 = mock.Mock(spec=backend.PlaybackProvider)
        self.backend2.playback = self.playback2

        self.tracks = [
            Track(uri="dummy1:a", length=40000),
            Track(uri="dummy2:a", length=40000),
        ]

        self.core = core.Core(
            config, mixer=None, backends=[self.backend1, self.backend2]
        )

        with deprecation.ignore():
            self.tl_tracks = self.core.tracklist.add(tracks=self.tracks)

    def trigger_stream_changed(self):
        pending = self.core.playback._pending_tl_track
        if pending:
            self.core.stream_changed(uri=pending.track.uri)
        else:
            self.core.stream_changed(uri=None)

    def test_play_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])
        self.trigger_stream_changed()

        self.playback1.prepare_change.assert_called_once_with()
        self.playback1.change_track.assert_called_once_with(self.tracks[0])
        self.playback1.play.assert_called_once_with()
        assert not self.playback2.play.called

    def test_play_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])
        self.trigger_stream_changed()

        assert not self.playback1.play.called
        self.playback2.prepare_change.assert_called_once_with()
        self.playback2.change_track.assert_called_once_with(self.tracks[1])
        self.playback2.play.assert_called_once_with()

    def test_pause_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])
        self.trigger_stream_changed()

        self.core.playback.pause()

        self.playback1.pause.assert_called_once_with()
        assert not self.playback2.pause.called

    def test_pause_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])
        self.trigger_stream_changed()

        self.core.playback.pause()

        assert not self.playback1.pause.called
        self.playback2.pause.assert_called_once_with()

    def test_resume_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])
        self.trigger_stream_changed()

        self.core.playback.pause()
        self.core.playback.resume()

        self.playback1.resume.assert_called_once_with()
        assert not self.playback2.resume.called

    def test_resume_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])
        self.trigger_stream_changed()

        self.core.playback.pause()
        self.core.playback.resume()

        assert not self.playback1.resume.called
        self.playback2.resume.assert_called_once_with()

    def test_stop_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])
        self.trigger_stream_changed()

        self.core.playback.stop()
        self.trigger_stream_changed()

        self.playback1.stop.assert_called_once_with()
        assert not self.playback2.stop.called

    def test_stop_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])
        self.trigger_stream_changed()

        self.core.playback.stop()
        self.trigger_stream_changed()

        assert not self.playback1.stop.called
        self.playback2.stop.assert_called_once_with()

    def test_seek_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])
        self.trigger_stream_changed()

        self.core.playback.seek(10000)

        self.playback1.seek.assert_called_once_with(10000)
        assert not self.playback2.seek.called

    def test_seek_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])
        self.trigger_stream_changed()

        self.core.playback.seek(10000)

        assert not self.playback1.seek.called
        self.playback2.seek.assert_called_once_with(10000)

    def test_time_position_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])
        self.trigger_stream_changed()

        self.core.playback.get_time_position()

        self.playback1.get_time_position.assert_called_once_with()
        assert not self.playback2.get_time_position.called

    def test_time_position_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])
        self.trigger_stream_changed()

        self.core.playback.get_time_position()

        assert not self.playback1.get_time_position.called
        self.playback2.get_time_position.assert_called_once_with()


class TestCorePlaybackWithOldBackend:
    def test_type_error_from_old_backend_does_not_crash_core(self):
        config = {"core": {"max_tracklist_length": 10000}}

        b = mock.Mock()
        b.actor_ref.actor_class.__name__ = "DummyBackend"
        b.uri_schemes.get.return_value = ["dummy1"]
        b.playback = mock.Mock(spec=backend.PlaybackProvider)
        b.playback.play.side_effect = TypeError
        b.library.lookup.return_value.get.return_value = [
            Track(uri="dummy1:a", length=40000)
        ]

        c = core.Core(config, mixer=None, backends=[b])
        c.tracklist.add(uris=["dummy1:a"])
        c.playback.play()  # No TypeError == test passed.
        b.playback.play.assert_called_once_with()


class TestBug1177Regression:
    def test(self):
        config = {"core": {"max_tracklist_length": 10000}}

        b = mock.Mock()
        b.uri_schemes.get.return_value = ["dummy"]
        b.playback = mock.Mock(spec=backend.PlaybackProvider)
        b.playback.change_track.return_value.get.return_value = True
        b.playback.play.return_value.get.return_value = True

        track1 = Track(uri="dummy:a", length=40000)
        track2 = Track(uri="dummy:b", length=40000)

        c = core.Core(config, mixer=None, backends=[b])
        with deprecation.ignore():
            c.tracklist.add(tracks=[track1, track2])

        c.playback.play()
        b.playback.change_track.assert_called_once_with(track1)
        b.playback.change_track.reset_mock()

        c.playback.pause()
        c.playback.next()
        b.playback.change_track.assert_called_once_with(track2)


class TestCorePlaybackSaveLoadState(BaseTest):
    def test_save(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.play(tl_tracks[1])
        self.replay_events()

        state = PlaybackState(
            time_position=0, state="playing", tlid=tl_tracks[1].tlid
        )
        value = self.core.playback._save_state()

        assert state == value

    def test_load(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.stop()
        self.replay_events()
        assert "stopped" == self.core.playback.get_state()

        state = PlaybackState(
            time_position=0, state="playing", tlid=tl_tracks[2].tlid
        )
        coverage = ["play-last"]
        self.core.playback._load_state(state, coverage)
        self.replay_events()

        assert "playing" == self.core.playback.get_state()
        assert tl_tracks[2] == self.core.playback.get_current_tl_track()

    def test_load_not_covered(self):
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.core.playback.stop()
        self.replay_events()
        assert "stopped" == self.core.playback.get_state()

        state = PlaybackState(
            time_position=0, state="playing", tlid=tl_tracks[2].tlid
        )
        coverage = ["other"]
        self.core.playback._load_state(state, coverage)
        self.replay_events()

        assert "stopped" == self.core.playback.get_state()
        assert self.core.playback.get_current_tl_track() is None

    def test_load_invalid_type(self):
        with pytest.raises(TypeError):
            self.core.playback._load_state(11, None)

    def test_load_none(self):
        self.core.playback._load_state(None, None)


class TestBug1352Regression(BaseTest):
    tracks = [
        Track(uri="dummy:a", length=40000),
        Track(uri="dummy:b", length=40000),
    ]

    def test_next_when_paused_updates_history(self):
        self.core.history._add_track = mock.Mock()
        self.core.tracklist._mark_playing = mock.Mock()
        tl_tracks = self.core.tracklist.get_tl_tracks()

        self.playback.play()
        self.replay_events()

        self.core.history._add_track.assert_called_once_with(self.tracks[0])
        self.core.tracklist._mark_playing.assert_called_once_with(tl_tracks[0])
        self.core.history._add_track.reset_mock()
        self.core.tracklist._mark_playing.reset_mock()

        self.playback.pause()
        self.playback.next()
        self.replay_events()

        self.core.history._add_track.assert_called_once_with(self.tracks[1])
        self.core.tracklist._mark_playing.assert_called_once_with(tl_tracks[1])


class TestEndlessLoop(BaseTest):

    tracks_play = [
        Track(uri="dummy:limit_never:a"),
        Track(uri="dummy:limit_never:b"),
    ]

    tracks_other = [
        Track(uri="dummy:limit_never:a"),
        Track(uri="dummy:limit_one"),
        Track(uri="dummy:limit_never:b"),
    ]

    def test_play(self):
        self.core.tracklist.clear()
        with deprecation.ignore():
            self.core.tracklist.add(tracks=self.tracks_play)

        self.backend.playback.reset_call_limit().get()
        self.core.tracklist.set_repeat(True)

        tl_tracks = self.core.tracklist.get_tl_tracks()
        self.core.playback.play(tl_tracks[0])
        self.replay_events()

        assert not self.backend.playback.is_call_limit_reached().get()

    def test_next(self):
        self.core.tracklist.clear()
        with deprecation.ignore():
            self.core.tracklist.add(tracks=self.tracks_other)

        self.backend.playback.reset_call_limit().get()
        self.core.tracklist.set_repeat(True)

        tl_tracks = self.core.tracklist.get_tl_tracks()
        self.core.playback.play(tl_tracks[1])
        self.replay_events()

        self.core.playback.next()
        self.replay_events()

        assert not self.backend.playback.is_call_limit_reached().get()

    def test_previous(self):
        self.core.tracklist.clear()
        with deprecation.ignore():
            self.core.tracklist.add(tracks=self.tracks_other)

        self.backend.playback.reset_call_limit().get()
        self.core.tracklist.set_repeat(True)

        tl_tracks = self.core.tracklist.get_tl_tracks()
        self.core.playback.play(tl_tracks[1])
        self.replay_events()

        self.core.playback.previous()
        self.replay_events()

        assert not self.backend.playback.is_call_limit_reached().get()

    def test_on_about_to_finish(self):
        self.core.tracklist.clear()
        with deprecation.ignore():
            self.core.tracklist.add(tracks=self.tracks_other)

        self.backend.playback.reset_call_limit().get()
        self.core.tracklist.set_repeat(True)

        tl_tracks = self.core.tracklist.get_tl_tracks()
        self.core.playback.play(tl_tracks[1])
        self.replay_events()

        self.trigger_about_to_finish()

        assert not self.backend.playback.is_call_limit_reached().get()
