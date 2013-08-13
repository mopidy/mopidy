from __future__ import unicode_literals

import mock
import random
import time
import unittest

import pykka

from mopidy import audio, core
from mopidy.core import PlaybackState
from mopidy.models import Track

from tests.backends.base import populate_tracklist

# TODO Test 'playlist repeat', e.g. repeat=1,single=0


class PlaybackControllerTest(object):
    tracks = []
    config = {}

    def setUp(self):
        self.audio = audio.DummyAudio.start().proxy()
        self.backend = self.backend_class.start(
            config=self.config, audio=self.audio).proxy()
        self.core = core.Core(backends=[self.backend])
        self.playback = self.core.playback
        self.tracklist = self.core.tracklist

        assert len(self.tracks) >= 3, \
            'Need at least three tracks to run tests.'
        assert self.tracks[0].length >= 2000, \
            'First song needs to be at least 2000 miliseconds'

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_initial_state_is_stopped(self):
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    def test_play_with_empty_playlist(self):
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)
        self.playback.play()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    def test_play_with_empty_playlist_return_value(self):
        self.assertEqual(self.playback.play(), None)

    @populate_tracklist
    def test_play_state(self):
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)
        self.playback.play()
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)

    @populate_tracklist
    def test_play_return_value(self):
        self.assertEqual(self.playback.play(), None)

    @populate_tracklist
    def test_play_track_state(self):
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)
        self.playback.play(self.tracklist.tl_tracks[-1])
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)

    @populate_tracklist
    def test_play_track_return_value(self):
        self.assertEqual(self.playback.play(
            self.tracklist.tl_tracks[-1]), None)

    @populate_tracklist
    def test_play_when_playing(self):
        self.playback.play()
        track = self.playback.current_track
        self.playback.play()
        self.assertEqual(track, self.playback.current_track)

    @populate_tracklist
    def test_play_when_paused(self):
        self.playback.play()
        track = self.playback.current_track
        self.playback.pause()
        self.playback.play()
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)
        self.assertEqual(track, self.playback.current_track)

    @populate_tracklist
    def test_play_when_pause_after_next(self):
        self.playback.play()
        self.playback.next()
        self.playback.next()
        track = self.playback.current_track
        self.playback.pause()
        self.playback.play()
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)
        self.assertEqual(track, self.playback.current_track)

    @populate_tracklist
    def test_play_sets_current_track(self):
        self.playback.play()
        self.assertEqual(self.playback.current_track, self.tracks[0])

    @populate_tracklist
    def test_play_track_sets_current_track(self):
        self.playback.play(self.tracklist.tl_tracks[-1])
        self.assertEqual(self.playback.current_track, self.tracks[-1])

    @populate_tracklist
    def test_play_skips_to_next_track_on_failure(self):
        # If backend's play() returns False, it is a failure.
        self.backend.playback.play = lambda track: track != self.tracks[0]
        self.playback.play()
        self.assertNotEqual(self.playback.current_track, self.tracks[0])
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_tracklist
    def test_current_track_after_completed_playlist(self):
        self.playback.play(self.tracklist.tl_tracks[-1])
        self.playback.on_end_of_track()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)
        self.assertEqual(self.playback.current_track, None)

        self.playback.play(self.tracklist.tl_tracks[-1])
        self.playback.next()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)
        self.assertEqual(self.playback.current_track, None)

    @populate_tracklist
    def test_previous(self):
        self.playback.play()
        self.playback.next()
        self.playback.previous()
        self.assertEqual(self.playback.current_track, self.tracks[0])

    @populate_tracklist
    def test_previous_more(self):
        self.playback.play()  # At track 0
        self.playback.next()  # At track 1
        self.playback.next()  # At track 2
        self.playback.previous()  # At track 1
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_tracklist
    def test_previous_return_value(self):
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.previous(), None)

    @populate_tracklist
    def test_previous_does_not_trigger_playback(self):
        self.playback.play()
        self.playback.next()
        self.playback.stop()
        self.playback.previous()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    @populate_tracklist
    def test_previous_at_start_of_playlist(self):
        self.playback.previous()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)
        self.assertEqual(self.playback.current_track, None)

    def test_previous_for_empty_playlist(self):
        self.playback.previous()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)
        self.assertEqual(self.playback.current_track, None)

    @populate_tracklist
    def test_previous_skips_to_previous_track_on_failure(self):
        # If backend's play() returns False, it is a failure.
        self.backend.playback.play = lambda track: track != self.tracks[1]
        self.playback.play(self.tracklist.tl_tracks[2])
        self.assertEqual(self.playback.current_track, self.tracks[2])
        self.playback.previous()
        self.assertNotEqual(self.playback.current_track, self.tracks[1])
        self.assertEqual(self.playback.current_track, self.tracks[0])

    @populate_tracklist
    def test_next(self):
        self.playback.play()

        tl_track = self.playback.current_tl_track
        old_position = self.tracklist.index(tl_track)
        old_uri = tl_track.track.uri

        self.playback.next()

        tl_track = self.playback.current_tl_track
        self.assertEqual(
            self.tracklist.index(tl_track), old_position + 1)
        self.assertNotEqual(self.playback.current_track.uri, old_uri)

    @populate_tracklist
    def test_next_return_value(self):
        self.playback.play()
        self.assertEqual(self.playback.next(), None)

    @populate_tracklist
    def test_next_does_not_trigger_playback(self):
        self.playback.next()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    @populate_tracklist
    def test_next_at_end_of_playlist(self):
        self.playback.play()

        for i, track in enumerate(self.tracks):
            self.assertEqual(self.playback.state, PlaybackState.PLAYING)
            self.assertEqual(self.playback.current_track, track)
            tl_track = self.playback.current_tl_track
            self.assertEqual(self.tracklist.index(tl_track), i)

            self.playback.next()

        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    @populate_tracklist
    def test_next_until_end_of_playlist_and_play_from_start(self):
        self.playback.play()

        for _ in self.tracks:
            self.playback.next()

        self.assertEqual(self.playback.current_track, None)
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

        self.playback.play()
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)
        self.assertEqual(self.playback.current_track, self.tracks[0])

    def test_next_for_empty_playlist(self):
        self.playback.next()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    @populate_tracklist
    def test_next_skips_to_next_track_on_failure(self):
        # If backend's play() returns False, it is a failure.
        self.backend.playback.play = lambda track: track != self.tracks[1]
        self.playback.play()
        self.assertEqual(self.playback.current_track, self.tracks[0])
        self.playback.next()
        self.assertNotEqual(self.playback.current_track, self.tracks[1])
        self.assertEqual(self.playback.current_track, self.tracks[2])

    @populate_tracklist
    def test_end_of_track(self):
        self.playback.play()

        tl_track = self.playback.current_tl_track
        old_position = self.tracklist.index(tl_track)
        old_uri = tl_track.track.uri

        self.playback.on_end_of_track()

        tl_track = self.playback.current_tl_track
        self.assertEqual(
            self.tracklist.index(tl_track), old_position + 1)
        self.assertNotEqual(self.playback.current_track.uri, old_uri)

    @populate_tracklist
    def test_end_of_track_return_value(self):
        self.playback.play()
        self.assertEqual(self.playback.on_end_of_track(), None)

    @populate_tracklist
    def test_end_of_track_does_not_trigger_playback(self):
        self.playback.on_end_of_track()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    @populate_tracklist
    def test_end_of_track_at_end_of_playlist(self):
        self.playback.play()

        for i, track in enumerate(self.tracks):
            self.assertEqual(self.playback.state, PlaybackState.PLAYING)
            self.assertEqual(self.playback.current_track, track)
            tl_track = self.playback.current_tl_track
            self.assertEqual(self.tracklist.index(tl_track), i)

            self.playback.on_end_of_track()

        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    @populate_tracklist
    def test_end_of_track_until_end_of_playlist_and_play_from_start(self):
        self.playback.play()

        for _ in self.tracks:
            self.playback.on_end_of_track()

        self.assertEqual(self.playback.current_track, None)
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

        self.playback.play()
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)
        self.assertEqual(self.playback.current_track, self.tracks[0])

    def test_end_of_track_for_empty_playlist(self):
        self.playback.on_end_of_track()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    @populate_tracklist
    def test_end_of_track_skips_to_next_track_on_failure(self):
        # If backend's play() returns False, it is a failure.
        self.backend.playback.play = lambda track: track != self.tracks[1]
        self.playback.play()
        self.assertEqual(self.playback.current_track, self.tracks[0])
        self.playback.on_end_of_track()
        self.assertNotEqual(self.playback.current_track, self.tracks[1])
        self.assertEqual(self.playback.current_track, self.tracks[2])

    @populate_tracklist
    def test_initial_current_track(self):
        self.assertEqual(self.playback.current_track, None)

    @populate_tracklist
    def test_current_track_during_play(self):
        self.playback.play()
        self.assertEqual(self.playback.current_track, self.tracks[0])

    @populate_tracklist
    def test_current_track_after_next(self):
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_tracklist
    def test_initial_index(self):
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.index(tl_track), None)

    @populate_tracklist
    def test_index_during_play(self):
        self.playback.play()
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.index(tl_track), 0)

    @populate_tracklist
    def test_index_after_next(self):
        self.playback.play()
        self.playback.next()
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.index(tl_track), 1)

    @populate_tracklist
    def test_index_at_end_of_playlist(self):
        self.playback.play(self.tracklist.tl_tracks[-1])
        self.playback.on_end_of_track()
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.index(tl_track), None)

    def test_on_tracklist_change_gets_called(self):
        callback = self.playback.on_tracklist_change

        def wrapper():
            wrapper.called = True
            return callback()
        wrapper.called = False

        self.playback.on_tracklist_change = wrapper
        self.tracklist.add([Track()])

        self.assert_(wrapper.called)

    @unittest.SkipTest  # Blocks for 10ms
    @populate_tracklist
    def test_end_of_track_callback_gets_called(self):
        self.playback.play()
        result = self.playback.seek(self.tracks[0].length - 10)
        self.assertTrue(result, 'Seek failed')
        message = self.core_queue.get(True, 1)
        self.assertEqual('end_of_track', message['command'])

    @populate_tracklist
    def test_on_tracklist_change_when_playing(self):
        self.playback.play()
        current_track = self.playback.current_track
        self.tracklist.add([self.tracks[2]])
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)
        self.assertEqual(self.playback.current_track, current_track)

    @populate_tracklist
    def test_on_tracklist_change_when_stopped(self):
        self.tracklist.add([self.tracks[2]])
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)
        self.assertEqual(self.playback.current_track, None)

    @populate_tracklist
    def test_on_tracklist_change_when_paused(self):
        self.playback.play()
        self.playback.pause()
        current_track = self.playback.current_track
        self.tracklist.add([self.tracks[2]])
        self.assertEqual(self.playback.state, PlaybackState.PAUSED)
        self.assertEqual(self.playback.current_track, current_track)

    @populate_tracklist
    def test_pause_when_stopped(self):
        self.playback.pause()
        self.assertEqual(self.playback.state, PlaybackState.PAUSED)

    @populate_tracklist
    def test_pause_when_playing(self):
        self.playback.play()
        self.playback.pause()
        self.assertEqual(self.playback.state, PlaybackState.PAUSED)

    @populate_tracklist
    def test_pause_when_paused(self):
        self.playback.play()
        self.playback.pause()
        self.playback.pause()
        self.assertEqual(self.playback.state, PlaybackState.PAUSED)

    @populate_tracklist
    def test_pause_return_value(self):
        self.playback.play()
        self.assertEqual(self.playback.pause(), None)

    @populate_tracklist
    def test_resume_when_stopped(self):
        self.playback.resume()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    @populate_tracklist
    def test_resume_when_playing(self):
        self.playback.play()
        self.playback.resume()
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)

    @populate_tracklist
    def test_resume_when_paused(self):
        self.playback.play()
        self.playback.pause()
        self.playback.resume()
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)

    @populate_tracklist
    def test_resume_return_value(self):
        self.playback.play()
        self.playback.pause()
        self.assertEqual(self.playback.resume(), None)

    @unittest.SkipTest  # Uses sleep and might not work with LocalBackend
    @populate_tracklist
    def test_resume_continues_from_right_position(self):
        self.playback.play()
        time.sleep(0.2)
        self.playback.pause()
        self.playback.resume()
        self.assertNotEqual(self.playback.time_position, 0)

    @populate_tracklist
    def test_seek_when_stopped(self):
        result = self.playback.seek(1000)
        self.assert_(result, 'Seek return value was %s' % result)

    @populate_tracklist
    def test_seek_when_stopped_updates_position(self):
        self.playback.seek(1000)
        position = self.playback.time_position
        self.assertGreaterEqual(position, 990)

    def test_seek_on_empty_playlist(self):
        self.assertFalse(self.playback.seek(0))

    def test_seek_on_empty_playlist_updates_position(self):
        self.playback.seek(0)
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    @populate_tracklist
    def test_seek_when_stopped_triggers_play(self):
        self.playback.seek(0)
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)

    @populate_tracklist
    def test_seek_when_playing(self):
        self.playback.play()
        result = self.playback.seek(self.tracks[0].length - 1000)
        self.assert_(result, 'Seek return value was %s' % result)

    @populate_tracklist
    def test_seek_when_playing_updates_position(self):
        length = self.tracklist.tracks[0].length
        self.playback.play()
        self.playback.seek(length - 1000)
        position = self.playback.time_position
        self.assertGreaterEqual(position, length - 1010)

    @populate_tracklist
    def test_seek_when_paused(self):
        self.playback.play()
        self.playback.pause()
        result = self.playback.seek(self.tracks[0].length - 1000)
        self.assert_(result, 'Seek return value was %s' % result)

    @populate_tracklist
    def test_seek_when_paused_updates_position(self):
        length = self.tracklist.tracks[0].length
        self.playback.play()
        self.playback.pause()
        self.playback.seek(length - 1000)
        position = self.playback.time_position
        self.assertGreaterEqual(position, length - 1010)

    @populate_tracklist
    def test_seek_when_paused_triggers_play(self):
        self.playback.play()
        self.playback.pause()
        self.playback.seek(0)
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)

    @unittest.SkipTest
    @populate_tracklist
    def test_seek_beyond_end_of_song(self):
        # FIXME need to decide return value
        self.playback.play()
        result = self.playback.seek(self.tracks[0].length * 100)
        self.assert_(not result, 'Seek return value was %s' % result)

    @populate_tracklist
    def test_seek_beyond_end_of_song_jumps_to_next_song(self):
        self.playback.play()
        self.playback.seek(self.tracks[0].length * 100)
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_tracklist
    def test_seek_beyond_end_of_song_for_last_track(self):
        self.playback.play(self.tracklist.tl_tracks[-1])
        self.playback.seek(self.tracklist.tracks[-1].length * 100)
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    @unittest.SkipTest
    @populate_tracklist
    def test_seek_beyond_start_of_song(self):
        # FIXME need to decide return value
        self.playback.play()
        result = self.playback.seek(-1000)
        self.assert_(not result, 'Seek return value was %s' % result)

    @populate_tracklist
    def test_seek_beyond_start_of_song_update_postion(self):
        self.playback.play()
        self.playback.seek(-1000)
        position = self.playback.time_position
        self.assertGreaterEqual(position, 0)
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)

    @populate_tracklist
    def test_stop_when_stopped(self):
        self.playback.stop()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    @populate_tracklist
    def test_stop_when_playing(self):
        self.playback.play()
        self.playback.stop()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    @populate_tracklist
    def test_stop_when_paused(self):
        self.playback.play()
        self.playback.pause()
        self.playback.stop()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    def test_stop_return_value(self):
        self.playback.play()
        self.assertEqual(self.playback.stop(), None)

    def test_time_position_when_stopped(self):
        future = mock.Mock()
        future.get = mock.Mock(return_value=0)
        self.audio.get_position = mock.Mock(return_value=future)

        self.assertEqual(self.playback.time_position, 0)

    @populate_tracklist
    def test_time_position_when_stopped_with_playlist(self):
        future = mock.Mock()
        future.get = mock.Mock(return_value=0)
        self.audio.get_position = mock.Mock(return_value=future)

        self.assertEqual(self.playback.time_position, 0)

    @unittest.SkipTest  # Uses sleep and does might not work with LocalBackend
    @populate_tracklist
    def test_time_position_when_playing(self):
        self.playback.play()
        first = self.playback.time_position
        time.sleep(1)
        second = self.playback.time_position
        self.assertGreater(second, first)

    @unittest.SkipTest  # Uses sleep
    @populate_tracklist
    def test_time_position_when_paused(self):
        self.playback.play()
        time.sleep(0.2)
        self.playback.pause()
        time.sleep(0.2)
        first = self.playback.time_position
        second = self.playback.time_position
        self.assertEqual(first, second)

    @populate_tracklist
    def test_play_with_consume(self):
        self.tracklist.consume = True
        self.playback.play()
        self.assertEqual(self.playback.current_track, self.tracks[0])

    @populate_tracklist
    def test_playlist_is_empty_after_all_tracks_are_played_with_consume(self):
        self.tracklist.consume = True
        self.playback.play()
        for _ in range(len(self.tracklist.tracks)):
            self.playback.on_end_of_track()
        self.assertEqual(len(self.tracklist.tracks), 0)

    @populate_tracklist
    def test_play_with_random(self):
        random.seed(1)
        self.tracklist.random = True
        self.playback.play()
        self.assertEqual(self.playback.current_track, self.tracks[2])

    @populate_tracklist
    def test_previous_with_random(self):
        random.seed(1)
        self.tracklist.random = True
        self.playback.play()
        self.playback.next()
        current_track = self.playback.current_track
        self.playback.previous()
        self.assertEqual(self.playback.current_track, current_track)

    @populate_tracklist
    def test_end_of_song_starts_next_track(self):
        self.playback.play()
        self.playback.on_end_of_track()
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_tracklist
    def test_end_of_song_with_single_and_repeat_starts_same(self):
        self.tracklist.single = True
        self.tracklist.repeat = True
        self.playback.play()
        self.playback.on_end_of_track()
        self.assertEqual(self.playback.current_track, self.tracks[0])

    @populate_tracklist
    def test_end_of_playlist_stops(self):
        self.playback.play(self.tracklist.tl_tracks[-1])
        self.playback.on_end_of_track()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    def test_repeat_off_by_default(self):
        self.assertEqual(self.tracklist.repeat, False)

    def test_random_off_by_default(self):
        self.assertEqual(self.tracklist.random, False)

    def test_consume_off_by_default(self):
        self.assertEqual(self.tracklist.consume, False)

    @populate_tracklist
    def test_random_until_end_of_playlist(self):
        self.tracklist.random = True
        self.playback.play()
        for _ in self.tracks[1:]:
            self.playback.next()
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track), None)

    @populate_tracklist
    def test_random_until_end_of_playlist_and_play_from_start(self):
        self.tracklist.repeat = True
        for _ in self.tracks:
            self.playback.next()
        tl_track = self.playback.current_tl_track
        self.assertNotEqual(self.tracklist.next_track(tl_track), None)
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)
        self.playback.play()
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)

    @populate_tracklist
    def test_random_until_end_of_playlist_with_repeat(self):
        self.tracklist.repeat = True
        self.tracklist.random = True
        self.playback.play()
        for _ in self.tracks:
            self.playback.next()
        tl_track = self.playback.current_tl_track
        self.assertNotEqual(self.tracklist.next_track(tl_track), None)

    @populate_tracklist
    def test_played_track_during_random_not_played_again(self):
        self.tracklist.random = True
        self.playback.play()
        played = []
        for _ in self.tracks:
            self.assertNotIn(self.playback.current_track, played)
            played.append(self.playback.current_track)
            self.playback.next()

    @populate_tracklist
    def test_playing_track_that_isnt_in_playlist(self):
        test = lambda: self.playback.play((17, Track()))
        self.assertRaises(AssertionError, test)
