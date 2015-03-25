from __future__ import absolute_import, unicode_literals

import unittest

import mock

import pykka

from mopidy import backend, core
from mopidy.models import Track

from tests import dummy_audio as audio


# TODO: split into smaller easier to follow tests. setup is way to complex.
class CorePlaybackTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.backend1 = mock.Mock()
        self.backend1.uri_schemes.get.return_value = ['dummy1']
        self.playback1 = mock.Mock(spec=backend.PlaybackProvider)
        self.playback1.get_time_position().get.return_value = 1000
        self.playback1.reset_mock()
        self.backend1.playback = self.playback1

        self.backend2 = mock.Mock()
        self.backend2.uri_schemes.get.return_value = ['dummy2']
        self.playback2 = mock.Mock(spec=backend.PlaybackProvider)
        self.playback2.get_time_position().get.return_value = 2000
        self.playback2.reset_mock()
        self.backend2.playback = self.playback2

        # A backend without the optional playback provider
        self.backend3 = mock.Mock()
        self.backend3.uri_schemes.get.return_value = ['dummy3']
        self.backend3.has_playback().get.return_value = False

        self.tracks = [
            Track(uri='dummy1:a', length=40000),
            Track(uri='dummy2:a', length=40000),
            Track(uri='dummy3:a', length=40000),  # Unplayable
            Track(uri='dummy1:b', length=40000),
            Track(uri='dummy1:c', length=None),   # No duration
        ]

        self.core = core.Core(mixer=None, backends=[
            self.backend1, self.backend2, self.backend3])
        self.core.tracklist.add(self.tracks)

        self.tl_tracks = self.core.tracklist.tl_tracks
        self.unplayable_tl_track = self.tl_tracks[2]
        self.duration_less_tl_track = self.tl_tracks[4]

    def trigger_end_of_track(self):
        self.core.playback._on_end_of_track()

    def set_current_tl_track(self, tl_track):
        self.core.playback._set_current_tl_track(tl_track)

    def test_get_current_tl_track_none(self):
        self.set_current_tl_track(None)

        self.assertEqual(
            self.core.playback.get_current_tl_track(), None)

    def test_get_current_tl_track_play(self):
        self.core.playback.play(self.tl_tracks[0])

        self.assertEqual(
            self.core.playback.get_current_tl_track(), self.tl_tracks[0])

    def test_get_current_tl_track_next(self):
        self.core.playback.play(self.tl_tracks[0])
        self.core.playback.next()

        self.assertEqual(
            self.core.playback.get_current_tl_track(), self.tl_tracks[1])

    def test_get_current_tl_track_prev(self):
        self.core.playback.play(self.tl_tracks[1])
        self.core.playback.previous()

        self.assertEqual(
            self.core.playback.get_current_tl_track(), self.tl_tracks[0])

    def test_get_current_track_play(self):
        self.core.playback.play(self.tl_tracks[0])

        self.assertEqual(
            self.core.playback.get_current_track(), self.tracks[0])

    def test_get_current_track_next(self):
        self.core.playback.play(self.tl_tracks[0])
        self.core.playback.next()

        self.assertEqual(
            self.core.playback.get_current_track(), self.tracks[1])

    def test_get_current_track_prev(self):
        self.core.playback.play(self.tl_tracks[1])
        self.core.playback.previous()

        self.assertEqual(
            self.core.playback.get_current_track(), self.tracks[0])

    # TODO Test state

    def test_play_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])

        self.playback1.prepare_change.assert_called_once_with()
        self.playback1.change_track.assert_called_once_with(self.tracks[0])
        self.playback1.play.assert_called_once_with()
        self.assertFalse(self.playback2.play.called)

    def test_play_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])

        self.assertFalse(self.playback1.play.called)
        self.playback2.prepare_change.assert_called_once_with()
        self.playback2.change_track.assert_called_once_with(self.tracks[1])
        self.playback2.play.assert_called_once_with()

    def test_play_skips_to_next_on_track_without_playback_backend(self):
        self.core.playback.play(self.unplayable_tl_track)

        self.playback1.prepare_change.assert_called_once_with()
        self.playback1.change_track.assert_called_once_with(self.tracks[3])
        self.playback1.play.assert_called_once_with()
        self.assertFalse(self.playback2.play.called)

        self.assertEqual(
            self.core.playback.current_tl_track, self.tl_tracks[3])

    def test_play_skips_to_next_on_unplayable_track(self):
        """Checks that we handle backend.change_track failing."""
        self.playback2.change_track.return_value.get.return_value = False

        self.core.tracklist.clear()
        self.core.tracklist.add(self.tracks[:2])
        tl_tracks = self.core.tracklist.tl_tracks

        self.core.playback.play(tl_tracks[0])
        self.core.playback.play(tl_tracks[1])

        # TODO: we really want to check that the track was marked unplayable
        # and that next was called. This is just an indirect way of checking
        # this :(
        self.assertEqual(self.core.playback.state, core.PlaybackState.STOPPED)

    @mock.patch(
        'mopidy.core.playback.listener.CoreListener', spec=core.CoreListener)
    def test_play_when_stopped_emits_events(self, listener_mock):
        self.core.playback.play(self.tl_tracks[0])

        self.assertListEqual(
            listener_mock.send.mock_calls,
            [
                mock.call(
                    'playback_state_changed',
                    old_state='stopped', new_state='playing'),
                mock.call(
                    'track_playback_started', tl_track=self.tl_tracks[0]),
            ])

    @mock.patch(
        'mopidy.core.playback.listener.CoreListener', spec=core.CoreListener)
    def test_play_when_paused_emits_events(self, listener_mock):
        self.core.playback.play(self.tl_tracks[0])
        self.core.playback.pause()
        listener_mock.reset_mock()

        self.core.playback.play(self.tl_tracks[1])

        self.assertListEqual(
            listener_mock.send.mock_calls,
            [
                mock.call(
                    'playback_state_changed',
                    old_state='paused', new_state='playing'),
                mock.call(
                    'track_playback_started', tl_track=self.tl_tracks[1]),
            ])

    @mock.patch(
        'mopidy.core.playback.listener.CoreListener', spec=core.CoreListener)
    def test_play_when_playing_emits_events(self, listener_mock):
        self.core.playback.play(self.tl_tracks[0])
        listener_mock.reset_mock()

        self.core.playback.play(self.tl_tracks[3])

        self.assertListEqual(
            listener_mock.send.mock_calls,
            [
                mock.call(
                    'playback_state_changed',
                    old_state='playing', new_state='stopped'),
                mock.call(
                    'track_playback_ended',
                    tl_track=self.tl_tracks[0], time_position=1000),
                mock.call(
                    'playback_state_changed',
                    old_state='stopped', new_state='playing'),
                mock.call(
                    'track_playback_started', tl_track=self.tl_tracks[3]),
            ])

    def test_pause_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])
        self.core.playback.pause()

        self.playback1.pause.assert_called_once_with()
        self.assertFalse(self.playback2.pause.called)

    def test_pause_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])
        self.core.playback.pause()

        self.assertFalse(self.playback1.pause.called)
        self.playback2.pause.assert_called_once_with()

    def test_pause_changes_state_even_if_track_is_unplayable(self):
        self.set_current_tl_track(self.unplayable_tl_track)
        self.core.playback.pause()

        self.assertEqual(self.core.playback.state, core.PlaybackState.PAUSED)
        self.assertFalse(self.playback1.pause.called)
        self.assertFalse(self.playback2.pause.called)

    @mock.patch(
        'mopidy.core.playback.listener.CoreListener', spec=core.CoreListener)
    def test_pause_emits_events(self, listener_mock):
        self.core.playback.play(self.tl_tracks[0])
        listener_mock.reset_mock()

        self.core.playback.pause()

        self.assertListEqual(
            listener_mock.send.mock_calls,
            [
                mock.call(
                    'playback_state_changed',
                    old_state='playing', new_state='paused'),
                mock.call(
                    'track_playback_paused',
                    tl_track=self.tl_tracks[0], time_position=1000),
            ])

    def test_resume_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])
        self.core.playback.pause()
        self.core.playback.resume()

        self.playback1.resume.assert_called_once_with()
        self.assertFalse(self.playback2.resume.called)

    def test_resume_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])
        self.core.playback.pause()
        self.core.playback.resume()

        self.assertFalse(self.playback1.resume.called)
        self.playback2.resume.assert_called_once_with()

    def test_resume_does_nothing_if_track_is_unplayable(self):
        self.set_current_tl_track(self.unplayable_tl_track)
        self.core.playback.state = core.PlaybackState.PAUSED
        self.core.playback.resume()

        self.assertEqual(self.core.playback.state, core.PlaybackState.PAUSED)
        self.assertFalse(self.playback1.resume.called)
        self.assertFalse(self.playback2.resume.called)

    @mock.patch(
        'mopidy.core.playback.listener.CoreListener', spec=core.CoreListener)
    def test_resume_emits_events(self, listener_mock):
        self.core.playback.play(self.tl_tracks[0])
        self.core.playback.pause()
        listener_mock.reset_mock()

        self.core.playback.resume()

        self.assertListEqual(
            listener_mock.send.mock_calls,
            [
                mock.call(
                    'playback_state_changed',
                    old_state='paused', new_state='playing'),
                mock.call(
                    'track_playback_resumed',
                    tl_track=self.tl_tracks[0], time_position=1000),
            ])

    def test_stop_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])
        self.core.playback.stop()

        self.playback1.stop.assert_called_once_with()
        self.assertFalse(self.playback2.stop.called)

    def test_stop_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])
        self.core.playback.stop()

        self.assertFalse(self.playback1.stop.called)
        self.playback2.stop.assert_called_once_with()

    def test_stop_changes_state_even_if_track_is_unplayable(self):
        self.set_current_tl_track(self.unplayable_tl_track)
        self.core.playback.state = core.PlaybackState.PAUSED
        self.core.playback.stop()

        self.assertEqual(self.core.playback.state, core.PlaybackState.STOPPED)
        self.assertFalse(self.playback1.stop.called)
        self.assertFalse(self.playback2.stop.called)

    @mock.patch(
        'mopidy.core.playback.listener.CoreListener', spec=core.CoreListener)
    def test_stop_emits_events(self, listener_mock):
        self.core.playback.play(self.tl_tracks[0])
        listener_mock.reset_mock()

        self.core.playback.stop()

        self.assertListEqual(
            listener_mock.send.mock_calls,
            [
                mock.call(
                    'playback_state_changed',
                    old_state='playing', new_state='stopped'),
                mock.call(
                    'track_playback_ended',
                    tl_track=self.tl_tracks[0], time_position=1000),
            ])

    # TODO Test next() more

    def test_next_keeps_finished_track_in_tracklist(self):
        tl_track = self.tl_tracks[0]
        self.core.playback.play(tl_track)

        self.core.playback.next()

        self.assertIn(tl_track, self.core.tracklist.tl_tracks)

    def test_next_in_consume_mode_removes_finished_track(self):
        tl_track = self.tl_tracks[0]
        self.core.playback.play(tl_track)
        self.core.tracklist.consume = True

        self.core.playback.next()

        self.assertNotIn(tl_track, self.core.tracklist.tl_tracks)

    @mock.patch(
        'mopidy.core.playback.listener.CoreListener', spec=core.CoreListener)
    def test_next_emits_events(self, listener_mock):
        self.core.playback.play(self.tl_tracks[0])
        listener_mock.reset_mock()

        self.core.playback.next()

        self.assertListEqual(
            listener_mock.send.mock_calls,
            [
                mock.call(
                    'playback_state_changed',
                    old_state='playing', new_state='stopped'),
                mock.call(
                    'track_playback_ended',
                    tl_track=self.tl_tracks[0], time_position=mock.ANY),
                mock.call(
                    'playback_state_changed',
                    old_state='stopped', new_state='playing'),
                mock.call(
                    'track_playback_started', tl_track=self.tl_tracks[1]),
            ])

    # TODO Test previous() more

    def test_previous_keeps_finished_track_in_tracklist(self):
        tl_track = self.tl_tracks[1]
        self.core.playback.play(tl_track)

        self.core.playback.previous()

        self.assertIn(tl_track, self.core.tracklist.tl_tracks)

    def test_previous_keeps_finished_track_even_in_consume_mode(self):
        tl_track = self.tl_tracks[1]
        self.core.playback.play(tl_track)
        self.core.tracklist.consume = True

        self.core.playback.previous()

        self.assertIn(tl_track, self.core.tracklist.tl_tracks)

    @mock.patch(
        'mopidy.core.playback.listener.CoreListener', spec=core.CoreListener)
    def test_previous_emits_events(self, listener_mock):
        self.core.playback.play(self.tl_tracks[1])
        listener_mock.reset_mock()

        self.core.playback.previous()

        self.assertListEqual(
            listener_mock.send.mock_calls,
            [
                mock.call(
                    'playback_state_changed',
                    old_state='playing', new_state='stopped'),
                mock.call(
                    'track_playback_ended',
                    tl_track=self.tl_tracks[1], time_position=mock.ANY),
                mock.call(
                    'playback_state_changed',
                    old_state='stopped', new_state='playing'),
                mock.call(
                    'track_playback_started', tl_track=self.tl_tracks[0]),
            ])

    # TODO Test on_end_of_track() more

    def test_on_end_of_track_keeps_finished_track_in_tracklist(self):
        tl_track = self.tl_tracks[0]
        self.core.playback.play(tl_track)

        self.trigger_end_of_track()

        self.assertIn(tl_track, self.core.tracklist.tl_tracks)

    def test_on_end_of_track_in_consume_mode_removes_finished_track(self):
        tl_track = self.tl_tracks[0]
        self.core.playback.play(tl_track)
        self.core.tracklist.consume = True

        self.trigger_end_of_track()

        self.assertNotIn(tl_track, self.core.tracklist.tl_tracks)

    @mock.patch(
        'mopidy.core.playback.listener.CoreListener', spec=core.CoreListener)
    def test_on_end_of_track_emits_events(self, listener_mock):
        self.core.playback.play(self.tl_tracks[0])
        listener_mock.reset_mock()

        self.trigger_end_of_track()

        self.assertListEqual(
            listener_mock.send.mock_calls,
            [
                mock.call(
                    'playback_state_changed',
                    old_state='playing', new_state='stopped'),
                mock.call(
                    'track_playback_ended',
                    tl_track=self.tl_tracks[0], time_position=mock.ANY),
                mock.call(
                    'playback_state_changed',
                    old_state='stopped', new_state='playing'),
                mock.call(
                    'track_playback_started', tl_track=self.tl_tracks[1]),
            ])

    @mock.patch(
        'mopidy.core.playback.listener.CoreListener', spec=core.CoreListener)
    def test_seek_past_end_of_track_emits_events(self, listener_mock):
        self.core.playback.play(self.tl_tracks[0])
        listener_mock.reset_mock()

        self.core.playback.seek(self.tracks[0].length * 5)

        self.assertListEqual(
            listener_mock.send.mock_calls,
            [
                mock.call(
                    'playback_state_changed',
                    old_state='playing', new_state='stopped'),
                mock.call(
                    'track_playback_ended',
                    tl_track=self.tl_tracks[0], time_position=mock.ANY),
                mock.call(
                    'playback_state_changed',
                    old_state='stopped', new_state='playing'),
                mock.call(
                    'track_playback_started', tl_track=self.tl_tracks[1]),
            ])

    def test_seek_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])
        self.core.playback.seek(10000)

        self.playback1.seek.assert_called_once_with(10000)
        self.assertFalse(self.playback2.seek.called)

    def test_seek_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])
        self.core.playback.seek(10000)

        self.assertFalse(self.playback1.seek.called)
        self.playback2.seek.assert_called_once_with(10000)

    def test_seek_fails_for_unplayable_track(self):
        self.set_current_tl_track(self.unplayable_tl_track)
        self.core.playback.state = core.PlaybackState.PLAYING
        success = self.core.playback.seek(1000)

        self.assertFalse(success)
        self.assertFalse(self.playback1.seek.called)
        self.assertFalse(self.playback2.seek.called)

    def test_seek_fails_for_track_without_duration(self):
        self.set_current_tl_track(self.duration_less_tl_track)
        self.core.playback.state = core.PlaybackState.PLAYING
        success = self.core.playback.seek(1000)

        self.assertFalse(success)
        self.assertFalse(self.playback1.seek.called)
        self.assertFalse(self.playback2.seek.called)

    def test_seek_play_stay_playing(self):
        self.core.playback.play(self.tl_tracks[0])
        self.core.playback.state = core.PlaybackState.PLAYING
        self.core.playback.seek(1000)

        self.assertEqual(self.core.playback.state, core.PlaybackState.PLAYING)

    def test_seek_paused_stay_paused(self):
        self.core.playback.play(self.tl_tracks[0])
        self.core.playback.state = core.PlaybackState.PAUSED
        self.core.playback.seek(1000)

        self.assertEqual(self.core.playback.state, core.PlaybackState.PAUSED)

    @mock.patch(
        'mopidy.core.playback.listener.CoreListener', spec=core.CoreListener)
    def test_seek_emits_seeked_event(self, listener_mock):
        self.core.playback.play(self.tl_tracks[0])
        listener_mock.reset_mock()

        self.core.playback.seek(1000)

        listener_mock.send.assert_called_once_with(
            'seeked', time_position=1000)

    def test_time_position_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])
        self.core.playback.seek(10000)
        self.core.playback.time_position

        self.playback1.get_time_position.assert_called_once_with()
        self.assertFalse(self.playback2.get_time_position.called)

    def test_time_position_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])
        self.core.playback.seek(10000)
        self.core.playback.time_position

        self.assertFalse(self.playback1.get_time_position.called)
        self.playback2.get_time_position.assert_called_once_with()

    def test_time_position_returns_0_if_track_is_unplayable(self):
        self.set_current_tl_track(self.unplayable_tl_track)

        result = self.core.playback.time_position

        self.assertEqual(result, 0)
        self.assertFalse(self.playback1.get_time_position.called)
        self.assertFalse(self.playback2.get_time_position.called)

    # TODO Test on_tracklist_change


# Since we rely on our DummyAudio to actually emit events we need a "real"
# backend and not a mock so the right calls make it through to audio.
class TestBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes = ['dummy']

    def __init__(self, config, audio):
        super(TestBackend, self).__init__()
        self.playback = backend.PlaybackProvider(audio=audio, backend=self)


class TestStream(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.audio = audio.DummyAudio.start().proxy()
        self.backend = TestBackend.start(config={}, audio=self.audio).proxy()
        self.core = core.Core(audio=self.audio, backends=[self.backend])
        self.playback = self.core.playback

        self.tracks = [Track(uri='dummy:a', length=1234),
                       Track(uri='dummy:b', length=1234)]

        self.core.tracklist.add(self.tracks)

        self.events = []
        self.patcher = mock.patch('mopidy.audio.listener.AudioListener.send')
        self.send_mock = self.patcher.start()

        def send(event, **kwargs):
            self.events.append((event, kwargs))

        self.send_mock.side_effect = send

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()
        self.patcher.stop()

    def replay_audio_events(self):
        while self.events:
            event, kwargs = self.events.pop(0)
            self.core.on_event(event, **kwargs)

    def test_get_stream_title_before_playback(self):
        self.assertEqual(self.playback.get_stream_title(), None)

    def test_get_stream_title_during_playback(self):
        self.core.playback.play()

        self.replay_audio_events()
        self.assertEqual(self.playback.get_stream_title(), None)

    def test_get_stream_title_during_playback_with_tags_change(self):
        self.core.playback.play()
        self.audio.trigger_fake_tags_changed({'organization': ['baz']})
        self.audio.trigger_fake_tags_changed({'title': ['foobar']}).get()

        self.replay_audio_events()
        self.assertEqual(self.playback.get_stream_title(), 'foobar')

    def test_get_stream_title_after_next(self):
        self.core.playback.play()
        self.audio.trigger_fake_tags_changed({'organization': ['baz']})
        self.audio.trigger_fake_tags_changed({'title': ['foobar']}).get()
        self.core.playback.next()

        self.replay_audio_events()
        self.assertEqual(self.playback.get_stream_title(), None)

    def test_get_stream_title_after_next_with_tags_change(self):
        self.core.playback.play()
        self.audio.trigger_fake_tags_changed({'organization': ['baz']})
        self.audio.trigger_fake_tags_changed({'title': ['foo']}).get()
        self.core.playback.next()
        self.audio.trigger_fake_tags_changed({'organization': ['baz']})
        self.audio.trigger_fake_tags_changed({'title': ['bar']}).get()

        self.replay_audio_events()
        self.assertEqual(self.playback.get_stream_title(), 'bar')

    def test_get_stream_title_after_stop(self):
        self.core.playback.play()
        self.audio.trigger_fake_tags_changed({'organization': ['baz']})
        self.audio.trigger_fake_tags_changed({'title': ['foobar']}).get()
        self.core.playback.stop()

        self.replay_audio_events()
        self.assertEqual(self.playback.get_stream_title(), None)


class CorePlaybackWithOldBackendTest(unittest.TestCase):
    def test_type_error_from_old_backend_does_not_crash_core(self):
        b = mock.Mock()
        b.uri_schemes.get.return_value = ['dummy1']
        b.playback = mock.Mock(spec=backend.PlaybackProvider)
        b.playback.play.side_effect = TypeError

        c = core.Core(mixer=None, backends=[b])
        c.tracklist.add([Track(uri='dummy1:a', length=40000)])
        c.playback.play()  # No TypeError == test passed.
