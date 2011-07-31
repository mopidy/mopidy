import mock
import random
import time

from mopidy.models import Track
from mopidy.gstreamer import GStreamer

from tests import unittest
from tests.backends.base import populate_playlist

# TODO Test 'playlist repeat', e.g. repeat=1,single=0


class PlaybackControllerTest(object):
    tracks = []

    def setUp(self):
        self.backend = self.backend_class()
        self.backend.gstreamer = mock.Mock(spec=GStreamer)
        self.playback = self.backend.playback
        self.current_playlist = self.backend.current_playlist

        assert len(self.tracks) >= 3, \
            'Need at least three tracks to run tests.'
        assert self.tracks[0].length >= 2000, \
            'First song needs to be at least 2000 miliseconds'

    def test_initial_state_is_stopped(self):
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    def test_play_with_empty_playlist(self):
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    def test_play_with_empty_playlist_return_value(self):
        self.assertEqual(self.playback.play(), None)

    @populate_playlist
    def test_play_state(self):
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_play_return_value(self):
        self.assertEqual(self.playback.play(), None)

    @populate_playlist
    def test_play_track_state(self):
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.playback.play(self.current_playlist.cp_tracks[-1])
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_play_track_return_value(self):
        self.assertEqual(self.playback.play(
            self.current_playlist.cp_tracks[-1]), None)

    @populate_playlist
    def test_play_when_playing(self):
        self.playback.play()
        track = self.playback.current_track
        self.playback.play()
        self.assertEqual(track, self.playback.current_track)

    @populate_playlist
    def test_play_when_paused(self):
        self.playback.play()
        track = self.playback.current_track
        self.playback.pause()
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)
        self.assertEqual(track, self.playback.current_track)

    @populate_playlist
    def test_play_when_pause_after_next(self):
        self.playback.play()
        self.playback.next()
        self.playback.next()
        track = self.playback.current_track
        self.playback.pause()
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)
        self.assertEqual(track, self.playback.current_track)

    @populate_playlist
    def test_play_sets_current_track(self):
        self.playback.play()
        self.assertEqual(self.playback.current_track, self.tracks[0])

    @populate_playlist
    def test_play_track_sets_current_track(self):
        self.playback.play(self.current_playlist.cp_tracks[-1])
        self.assertEqual(self.playback.current_track, self.tracks[-1])

    @populate_playlist
    def test_play_skips_to_next_track_on_failure(self):
        # If provider.play() returns False, it is a failure.
        self.playback.provider.play = lambda track: track != self.tracks[0]
        self.playback.play()
        self.assertNotEqual(self.playback.current_track, self.tracks[0])
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_playlist
    def test_current_track_after_completed_playlist(self):
        self.playback.play(self.current_playlist.cp_tracks[-1])
        self.playback.on_end_of_track()
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.assertEqual(self.playback.current_track, None)

        self.playback.play(self.current_playlist.cp_tracks[-1])
        self.playback.next()
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.assertEqual(self.playback.current_track, None)

    @populate_playlist
    def test_previous(self):
        self.playback.play()
        self.playback.next()
        self.playback.previous()
        self.assertEqual(self.playback.current_track, self.tracks[0])

    @populate_playlist
    def test_previous_more(self):
        self.playback.play() # At track 0
        self.playback.next() # At track 1
        self.playback.next() # At track 2
        self.playback.previous() # At track 1
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_playlist
    def test_previous_return_value(self):
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.previous(), None)

    @populate_playlist
    def test_previous_does_not_trigger_playback(self):
        self.playback.play()
        self.playback.next()
        self.playback.stop()
        self.playback.previous()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_previous_at_start_of_playlist(self):
        self.playback.previous()
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.assertEqual(self.playback.current_track, None)

    def test_previous_for_empty_playlist(self):
        self.playback.previous()
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.assertEqual(self.playback.current_track, None)

    @populate_playlist
    def test_previous_skips_to_previous_track_on_failure(self):
        # If provider.play() returns False, it is a failure.
        self.playback.provider.play = lambda track: track != self.tracks[1]
        self.playback.play(self.current_playlist.cp_tracks[2])
        self.assertEqual(self.playback.current_track, self.tracks[2])
        self.playback.previous()
        self.assertNotEqual(self.playback.current_track, self.tracks[1])
        self.assertEqual(self.playback.current_track, self.tracks[0])

    @populate_playlist
    def test_next(self):
        self.playback.play()

        old_position = self.playback.current_playlist_position
        old_uri = self.playback.current_track.uri

        self.playback.next()

        self.assertEqual(self.playback.current_playlist_position,
            old_position+1)
        self.assertNotEqual(self.playback.current_track.uri, old_uri)

    @populate_playlist
    def test_next_return_value(self):
        self.playback.play()
        self.assertEqual(self.playback.next(), None)

    @populate_playlist
    def test_next_does_not_trigger_playback(self):
        self.playback.next()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_next_at_end_of_playlist(self):
        self.playback.play()

        for i, track in enumerate(self.tracks):
            self.assertEqual(self.playback.state, self.playback.PLAYING)
            self.assertEqual(self.playback.current_track, track)
            self.assertEqual(self.playback.current_playlist_position, i)

            self.playback.next()

        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_next_until_end_of_playlist_and_play_from_start(self):
        self.playback.play()

        for _ in self.tracks:
            self.playback.next()

        self.assertEqual(self.playback.current_track, None)
        self.assertEqual(self.playback.state, self.playback.STOPPED)

        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)
        self.assertEqual(self.playback.current_track, self.tracks[0])

    def test_next_for_empty_playlist(self):
        self.playback.next()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_next_skips_to_next_track_on_failure(self):
        # If provider.play() returns False, it is a failure.
        self.playback.provider.play = lambda track: track != self.tracks[1]
        self.playback.play()
        self.assertEqual(self.playback.current_track, self.tracks[0])
        self.playback.next()
        self.assertNotEqual(self.playback.current_track, self.tracks[1])
        self.assertEqual(self.playback.current_track, self.tracks[2])

    @populate_playlist
    def test_next_track_before_play(self):
        self.assertEqual(self.playback.track_at_next, self.tracks[0])

    @populate_playlist
    def test_next_track_during_play(self):
        self.playback.play()
        self.assertEqual(self.playback.track_at_next, self.tracks[1])

    @populate_playlist
    def test_next_track_after_previous(self):
        self.playback.play()
        self.playback.next()
        self.playback.previous()
        self.assertEqual(self.playback.track_at_next, self.tracks[1])

    def test_next_track_empty_playlist(self):
        self.assertEqual(self.playback.track_at_next, None)

    @populate_playlist
    def test_next_track_at_end_of_playlist(self):
        self.playback.play()
        for _ in self.current_playlist.cp_tracks[1:]:
            self.playback.next()
        self.assertEqual(self.playback.track_at_next, None)

    @populate_playlist
    def test_next_track_at_end_of_playlist_with_repeat(self):
        self.playback.repeat = True
        self.playback.play()
        for _ in self.tracks[1:]:
            self.playback.next()
        self.assertEqual(self.playback.track_at_next, self.tracks[0])

    @populate_playlist
    def test_next_track_with_random(self):
        random.seed(1)
        self.playback.random = True
        self.assertEqual(self.playback.track_at_next, self.tracks[2])

    @populate_playlist
    def test_next_with_consume(self):
        self.playback.consume = True
        self.playback.play()
        self.playback.next()
        self.assert_(self.tracks[0] in self.backend.current_playlist.tracks)

    @populate_playlist
    def test_next_with_single_and_repeat(self):
        self.playback.single = True
        self.playback.repeat = True
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_playlist
    def test_next_with_random(self):
        # FIXME feels very fragile
        random.seed(1)
        self.playback.random = True
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_playlist
    def test_next_track_with_random_after_append_playlist(self):
        random.seed(1)
        self.playback.random = True
        self.assertEqual(self.playback.track_at_next, self.tracks[2])
        self.backend.current_playlist.append(self.tracks[:1])
        self.assertEqual(self.playback.track_at_next, self.tracks[1])

    @populate_playlist
    def test_end_of_track(self):
        self.playback.play()

        old_position = self.playback.current_playlist_position
        old_uri = self.playback.current_track.uri

        self.playback.on_end_of_track()

        self.assertEqual(self.playback.current_playlist_position,
            old_position+1)
        self.assertNotEqual(self.playback.current_track.uri, old_uri)

    @populate_playlist
    def test_end_of_track_return_value(self):
        self.playback.play()
        self.assertEqual(self.playback.on_end_of_track(), None)

    @populate_playlist
    def test_end_of_track_does_not_trigger_playback(self):
        self.playback.on_end_of_track()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_end_of_track_at_end_of_playlist(self):
        self.playback.play()

        for i, track in enumerate(self.tracks):
            self.assertEqual(self.playback.state, self.playback.PLAYING)
            self.assertEqual(self.playback.current_track, track)
            self.assertEqual(self.playback.current_playlist_position, i)

            self.playback.on_end_of_track()

        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_end_of_track_until_end_of_playlist_and_play_from_start(self):
        self.playback.play()

        for _ in self.tracks:
            self.playback.on_end_of_track()

        self.assertEqual(self.playback.current_track, None)
        self.assertEqual(self.playback.state, self.playback.STOPPED)

        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)
        self.assertEqual(self.playback.current_track, self.tracks[0])

    def test_end_of_track_for_empty_playlist(self):
        self.playback.on_end_of_track()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_end_of_track_skips_to_next_track_on_failure(self):
        # If provider.play() returns False, it is a failure.
        self.playback.provider.play = lambda track: track != self.tracks[1]
        self.playback.play()
        self.assertEqual(self.playback.current_track, self.tracks[0])
        self.playback.on_end_of_track()
        self.assertNotEqual(self.playback.current_track, self.tracks[1])
        self.assertEqual(self.playback.current_track, self.tracks[2])

    @populate_playlist
    def test_end_of_track_track_before_play(self):
        self.assertEqual(self.playback.track_at_next, self.tracks[0])

    @populate_playlist
    def test_end_of_track_track_during_play(self):
        self.playback.play()
        self.assertEqual(self.playback.track_at_next, self.tracks[1])

    @populate_playlist
    def test_end_of_track_track_after_previous(self):
        self.playback.play()
        self.playback.on_end_of_track()
        self.playback.previous()
        self.assertEqual(self.playback.track_at_next, self.tracks[1])

    def test_end_of_track_track_empty_playlist(self):
        self.assertEqual(self.playback.track_at_next, None)

    @populate_playlist
    def test_end_of_track_track_at_end_of_playlist(self):
        self.playback.play()
        for _ in self.current_playlist.cp_tracks[1:]:
            self.playback.on_end_of_track()
        self.assertEqual(self.playback.track_at_next, None)

    @populate_playlist
    def test_end_of_track_track_at_end_of_playlist_with_repeat(self):
        self.playback.repeat = True
        self.playback.play()
        for _ in self.tracks[1:]:
            self.playback.on_end_of_track()
        self.assertEqual(self.playback.track_at_next, self.tracks[0])

    @populate_playlist
    def test_end_of_track_track_with_random(self):
        random.seed(1)
        self.playback.random = True
        self.assertEqual(self.playback.track_at_next, self.tracks[2])


    @populate_playlist
    def test_end_of_track_with_consume(self):
        self.playback.consume = True
        self.playback.play()
        self.playback.on_end_of_track()
        self.assert_(self.tracks[0] not in self.backend.current_playlist.tracks)

    @populate_playlist
    def test_end_of_track_with_random(self):
        # FIXME feels very fragile
        random.seed(1)
        self.playback.random = True
        self.playback.play()
        self.playback.on_end_of_track()
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_playlist
    def test_end_of_track_track_with_random_after_append_playlist(self):
        random.seed(1)
        self.playback.random = True
        self.assertEqual(self.playback.track_at_next, self.tracks[2])
        self.backend.current_playlist.append(self.tracks[:1])
        self.assertEqual(self.playback.track_at_next, self.tracks[1])

    @populate_playlist
    def test_previous_track_before_play(self):
        self.assertEqual(self.playback.track_at_previous, None)

    @populate_playlist
    def test_previous_track_after_play(self):
        self.playback.play()
        self.assertEqual(self.playback.track_at_previous, None)

    @populate_playlist
    def test_previous_track_after_next(self):
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.track_at_previous, self.tracks[0])

    @populate_playlist
    def test_previous_track_after_previous(self):
        self.playback.play() # At track 0
        self.playback.next() # At track 1
        self.playback.next() # At track 2
        self.playback.previous() # At track 1
        self.assertEqual(self.playback.track_at_previous, self.tracks[0])

    def test_previous_track_empty_playlist(self):
        self.assertEqual(self.playback.track_at_previous, None)

    @populate_playlist
    def test_previous_track_with_consume(self):
        self.playback.consume = True
        for _ in self.tracks:
            self.playback.next()
            self.assertEqual(self.playback.track_at_previous,
                self.playback.current_track)

    @populate_playlist
    def test_previous_track_with_random(self):
        self.playback.random = True
        for _ in self.tracks:
            self.playback.next()
            self.assertEqual(self.playback.track_at_previous,
                self.playback.current_track)

    @populate_playlist
    def test_initial_current_track(self):
        self.assertEqual(self.playback.current_track, None)

    @populate_playlist
    def test_current_track_during_play(self):
        self.playback.play()
        self.assertEqual(self.playback.current_track, self.tracks[0])

    @populate_playlist
    def test_current_track_after_next(self):
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_playlist
    def test_initial_current_playlist_position(self):
        self.assertEqual(self.playback.current_playlist_position, None)

    @populate_playlist
    def test_current_playlist_position_during_play(self):
        self.playback.play()
        self.assertEqual(self.playback.current_playlist_position, 0)

    @populate_playlist
    def test_current_playlist_position_after_next(self):
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.current_playlist_position, 1)

    @populate_playlist
    def test_current_playlist_position_at_end_of_playlist(self):
        self.playback.play(self.current_playlist.cp_tracks[-1])
        self.playback.on_end_of_track()
        self.assertEqual(self.playback.current_playlist_position, None)

    def test_on_current_playlist_change_gets_called(self):
        callback = self.playback.on_current_playlist_change

        def wrapper():
            wrapper.called = True
            return callback()
        wrapper.called = False

        self.playback.on_current_playlist_change = wrapper
        self.backend.current_playlist.append([Track()])

        self.assert_(wrapper.called)

    @unittest.SkipTest # Blocks for 10ms
    @populate_playlist
    def test_end_of_track_callback_gets_called(self):
        self.playback.play()
        result = self.playback.seek(self.tracks[0].length - 10)
        self.assertTrue(result, 'Seek failed')
        message = self.core_queue.get(True, 1)
        self.assertEqual('end_of_track', message['command'])

    @populate_playlist
    def test_on_current_playlist_change_when_playing(self):
        self.playback.play()
        current_track = self.playback.current_track
        self.backend.current_playlist.append([self.tracks[2]])
        self.assertEqual(self.playback.state, self.playback.PLAYING)
        self.assertEqual(self.playback.current_track, current_track)

    @populate_playlist
    def test_on_current_playlist_change_when_stopped(self):
        self.backend.current_playlist.append([self.tracks[2]])
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.assertEqual(self.playback.current_track, None)

    @populate_playlist
    def test_on_current_playlist_change_when_paused(self):
        self.playback.play()
        self.playback.pause()
        current_track = self.playback.current_track
        self.backend.current_playlist.append([self.tracks[2]])
        self.assertEqual(self.playback.state, self.backend.playback.PAUSED)
        self.assertEqual(self.playback.current_track, current_track)

    @populate_playlist
    def test_pause_when_stopped(self):
        self.playback.pause()
        self.assertEqual(self.playback.state, self.playback.PAUSED)

    @populate_playlist
    def test_pause_when_playing(self):
        self.playback.play()
        self.playback.pause()
        self.assertEqual(self.playback.state, self.playback.PAUSED)

    @populate_playlist
    def test_pause_when_paused(self):
        self.playback.play()
        self.playback.pause()
        self.playback.pause()
        self.assertEqual(self.playback.state, self.playback.PAUSED)

    @populate_playlist
    def test_pause_return_value(self):
        self.playback.play()
        self.assertEqual(self.playback.pause(), None)

    @populate_playlist
    def test_resume_when_stopped(self):
        self.playback.resume()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_resume_when_playing(self):
        self.playback.play()
        self.playback.resume()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_resume_when_paused(self):
        self.playback.play()
        self.playback.pause()
        self.playback.resume()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_resume_return_value(self):
        self.playback.play()
        self.playback.pause()
        self.assertEqual(self.playback.resume(), None)

    @unittest.SkipTest # Uses sleep and might not work with LocalBackend
    @populate_playlist
    def test_resume_continues_from_right_position(self):
        self.playback.play()
        time.sleep(0.2)
        self.playback.pause()
        self.playback.resume()
        self.assertNotEqual(self.playback.time_position, 0)

    @populate_playlist
    def test_seek_when_stopped(self):
        result = self.playback.seek(1000)
        self.assert_(result, 'Seek return value was %s' % result)

    @populate_playlist
    def test_seek_when_stopped_updates_position(self):
        self.playback.seek(1000)
        position = self.playback.time_position
        self.assert_(position >= 990, position)

    def test_seek_on_empty_playlist(self):
        self.assertFalse(self.playback.seek(0))

    def test_seek_on_empty_playlist_updates_position(self):
        self.playback.seek(0)
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_seek_when_stopped_triggers_play(self):
        self.playback.seek(0)
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_seek_when_playing(self):
        self.playback.play()
        result = self.playback.seek(self.tracks[0].length - 1000)
        self.assert_(result, 'Seek return value was %s' % result)

    @populate_playlist
    def test_seek_when_playing_updates_position(self):
        length = self.backend.current_playlist.tracks[0].length
        self.playback.play()
        self.playback.seek(length - 1000)
        position = self.playback.time_position
        self.assert_(position >= length - 1010, position)

    @populate_playlist
    def test_seek_when_paused(self):
        self.playback.play()
        self.playback.pause()
        result = self.playback.seek(self.tracks[0].length - 1000)
        self.assert_(result, 'Seek return value was %s' % result)

    @populate_playlist
    def test_seek_when_paused_updates_position(self):
        length = self.backend.current_playlist.tracks[0].length
        self.playback.play()
        self.playback.pause()
        self.playback.seek(length - 1000)
        position = self.playback.time_position
        self.assert_(position >= length - 1010, position)

    @populate_playlist
    def test_seek_when_paused_triggers_play(self):
        self.playback.play()
        self.playback.pause()
        self.playback.seek(0)
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @unittest.SkipTest
    @populate_playlist
    def test_seek_beyond_end_of_song(self):
        # FIXME need to decide return value
        self.playback.play()
        result = self.playback.seek(self.tracks[0].length*100)
        self.assert_(not result, 'Seek return value was %s' % result)

    @populate_playlist
    def test_seek_beyond_end_of_song_jumps_to_next_song(self):
        self.playback.play()
        self.playback.seek(self.tracks[0].length*100)
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_playlist
    def test_seek_beyond_end_of_song_for_last_track(self):
        self.playback.play(self.current_playlist.cp_tracks[-1])
        self.playback.seek(self.current_playlist.tracks[-1].length * 100)
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @unittest.SkipTest
    @populate_playlist
    def test_seek_beyond_start_of_song(self):
        # FIXME need to decide return value
        self.playback.play()
        result = self.playback.seek(-1000)
        self.assert_(not result, 'Seek return value was %s' % result)

    @populate_playlist
    def test_seek_beyond_start_of_song_update_postion(self):
        self.playback.play()
        self.playback.seek(-1000)
        position = self.playback.time_position
        self.assert_(position >= 0, position)
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_stop_when_stopped(self):
        self.playback.stop()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_stop_when_playing(self):
        self.playback.play()
        self.playback.stop()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_stop_when_paused(self):
        self.playback.play()
        self.playback.pause()
        self.playback.stop()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    def test_stop_return_value(self):
        self.playback.play()
        self.assertEqual(self.playback.stop(), None)

    def test_time_position_when_stopped(self):
        future = mock.Mock()
        future.get = mock.Mock(return_value=0)
        self.backend.gstreamer.get_position = mock.Mock(return_value=future)

        self.assertEqual(self.playback.time_position, 0)

    @populate_playlist
    def test_time_position_when_stopped_with_playlist(self):
        future = mock.Mock()
        future.get = mock.Mock(return_value=0)
        self.backend.gstreamer.get_position = mock.Mock(return_value=future)

        self.assertEqual(self.playback.time_position, 0)

    @unittest.SkipTest # Uses sleep and does might not work with LocalBackend
    @populate_playlist
    def test_time_position_when_playing(self):
        self.playback.play()
        first = self.playback.time_position
        time.sleep(1)
        second = self.playback.time_position
        self.assert_(second > first, '%s - %s' % (first, second))

    @unittest.SkipTest # Uses sleep
    @populate_playlist
    def test_time_position_when_paused(self):
        self.playback.play()
        time.sleep(0.2)
        self.playback.pause()
        time.sleep(0.2)
        first = self.playback.time_position
        second = self.playback.time_position
        self.assertEqual(first, second)

    @populate_playlist
    def test_play_with_consume(self):
        self.playback.consume = True
        self.playback.play()
        self.assertEqual(self.playback.current_track, self.tracks[0])

    @populate_playlist
    def test_playlist_is_empty_after_all_tracks_are_played_with_consume(self):
        self.playback.consume = True
        self.playback.play()
        for _ in range(len(self.backend.current_playlist.tracks)):
            self.playback.on_end_of_track()
        self.assertEqual(len(self.backend.current_playlist.tracks), 0)

    @populate_playlist
    def test_play_with_random(self):
        random.seed(1)
        self.playback.random = True
        self.playback.play()
        self.assertEqual(self.playback.current_track, self.tracks[2])

    @populate_playlist
    def test_previous_with_random(self):
        random.seed(1)
        self.playback.random = True
        self.playback.play()
        self.playback.next()
        current_track = self.playback.current_track
        self.playback.previous()
        self.assertEqual(self.playback.current_track, current_track)

    @populate_playlist
    def test_end_of_song_starts_next_track(self):
        self.playback.play()
        self.playback.on_end_of_track()
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_playlist
    def test_end_of_song_with_single_and_repeat_starts_same(self):
        self.playback.single = True
        self.playback.repeat = True
        self.playback.play()
        self.playback.on_end_of_track()
        self.assertEqual(self.playback.current_track, self.tracks[0])

    @populate_playlist
    def test_end_of_playlist_stops(self):
        self.playback.play(self.current_playlist.cp_tracks[-1])
        self.playback.on_end_of_track()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    def test_repeat_off_by_default(self):
        self.assertEqual(self.playback.repeat, False)

    def test_random_off_by_default(self):
        self.assertEqual(self.playback.random, False)

    def test_consume_off_by_default(self):
        self.assertEqual(self.playback.consume, False)

    @populate_playlist
    def test_random_until_end_of_playlist(self):
        self.playback.random = True
        self.playback.play()
        for _ in self.tracks[1:]:
            self.playback.next()
        self.assertEqual(self.playback.track_at_next, None)

    @populate_playlist
    def test_random_until_end_of_playlist_and_play_from_start(self):
        self.playback.repeat = True
        for _ in self.tracks:
            self.playback.next()
        self.assertNotEqual(self.playback.track_at_next, None)
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_random_until_end_of_playlist_with_repeat(self):
        self.playback.repeat = True
        self.playback.random = True
        self.playback.play()
        for _ in self.tracks:
            self.playback.next()
        self.assertNotEqual(self.playback.track_at_next, None)

    @populate_playlist
    def test_played_track_during_random_not_played_again(self):
        self.playback.random = True
        self.playback.play()
        played = []
        for _ in self.tracks:
            self.assert_(self.playback.current_track not in played)
            played.append(self.playback.current_track)
            self.playback.next()

    @populate_playlist
    def test_playing_track_that_isnt_in_playlist(self):
        test = lambda: self.playback.play((17, Track()))
        self.assertRaises(AssertionError, test)
