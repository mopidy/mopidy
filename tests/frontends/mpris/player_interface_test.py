import mock
import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.backends.base.playback import PlaybackController
from mopidy.frontends import mpris
from mopidy.mixers.dummy import DummyMixer
from mopidy.models import Track

PLAYING = PlaybackController.PLAYING
PAUSED = PlaybackController.PAUSED
STOPPED = PlaybackController.STOPPED

class PlayerInterfaceTest(unittest.TestCase):
    def setUp(self):
        mpris.MprisObject._connect_to_dbus = mock.Mock()
        self.mixer = DummyMixer.start().proxy()
        self.backend = DummyBackend.start().proxy()
        self.mpris = mpris.MprisObject()
        self.mpris._backend = self.backend

    def tearDown(self):
        self.backend.stop()
        self.mixer.stop()

    def test_get_playback_status_is_playing_when_playing(self):
        self.backend.playback.state = PLAYING
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'PlaybackStatus')
        self.assertEqual('Playing', result)

    def test_get_playback_status_is_paused_when_paused(self):
        self.backend.playback.state = PAUSED
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'PlaybackStatus')
        self.assertEqual('Paused', result)

    def test_get_playback_status_is_stopped_when_stopped(self):
        self.backend.playback.state = STOPPED
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'PlaybackStatus')
        self.assertEqual('Stopped', result)

    def test_get_loop_status_is_none_when_not_looping(self):
        self.backend.playback.repeat = False
        self.backend.playback.single = False
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'LoopStatus')
        self.assertEqual('None', result)

    def test_get_loop_status_is_track_when_looping_a_single_track(self):
        self.backend.playback.repeat = True
        self.backend.playback.single = True
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'LoopStatus')
        self.assertEqual('Track', result)

    def test_get_loop_status_is_playlist_when_looping_the_current_playlist(self):
        self.backend.playback.repeat = True
        self.backend.playback.single = False
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'LoopStatus')
        self.assertEqual('Playlist', result)

    def test_set_loop_status_is_ignored_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        self.backend.playback.repeat = True
        self.backend.playback.single = True
        self.mpris.Set(mpris.PLAYER_IFACE, 'LoopStatus', 'None')
        self.assertEquals(self.backend.playback.repeat.get(), True)
        self.assertEquals(self.backend.playback.single.get(), True)

    def test_set_loop_status_to_none_unsets_repeat_and_single(self):
        self.mpris.Set(mpris.PLAYER_IFACE, 'LoopStatus', 'None')
        self.assertEquals(self.backend.playback.repeat.get(), False)
        self.assertEquals(self.backend.playback.single.get(), False)

    def test_set_loop_status_to_track_sets_repeat_and_single(self):
        self.mpris.Set(mpris.PLAYER_IFACE, 'LoopStatus', 'Track')
        self.assertEquals(self.backend.playback.repeat.get(), True)
        self.assertEquals(self.backend.playback.single.get(), True)

    def test_set_loop_status_to_playlists_sets_repeat_and_not_single(self):
        self.mpris.Set(mpris.PLAYER_IFACE, 'LoopStatus', 'Playlist')
        self.assertEquals(self.backend.playback.repeat.get(), True)
        self.assertEquals(self.backend.playback.single.get(), False)

    def test_get_rate_is_greater_or_equal_than_minimum_rate(self):
        rate = self.mpris.Get(mpris.PLAYER_IFACE, 'Rate')
        minimum_rate = self.mpris.Get(mpris.PLAYER_IFACE, 'MinimumRate')
        self.assert_(rate >= minimum_rate)

    def test_get_rate_is_less_or_equal_than_maximum_rate(self):
        rate = self.mpris.Get(mpris.PLAYER_IFACE, 'Rate')
        maximum_rate = self.mpris.Get(mpris.PLAYER_IFACE, 'MaximumRate')
        self.assert_(rate >= maximum_rate)

    def test_set_rate_to_zero_pauses_playback(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.mpris.Set(mpris.PLAYER_IFACE, 'Rate', 0)
        self.assertEquals(self.backend.playback.state.get(), PAUSED)

    def test_get_shuffle_returns_true_if_shuffle_is_active(self):
        self.backend.playback.shuffle = True
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'Shuffle')
        self.assertTrue(result)

    def test_get_shuffle_returns_false_if_shuffle_is_inactive(self):
        self.backend.playback.shuffle = False
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'Shuffle')
        self.assertFalse(result)

    def test_set_shuffle_is_ignored_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        self.backend.playback.shuffle = False
        result = self.mpris.Set(mpris.PLAYER_IFACE, 'Shuffle', True)
        self.assertFalse(self.backend.playback.shuffle.get())

    def test_set_shuffle_to_true_activates_shuffle_mode(self):
        self.backend.playback.shuffle = False
        self.assertFalse(self.backend.playback.shuffle.get())
        result = self.mpris.Set(mpris.PLAYER_IFACE, 'Shuffle', True)
        self.assertTrue(self.backend.playback.shuffle.get())

    def test_set_shuffle_to_false_deactivates_shuffle_mode(self):
        self.backend.playback.shuffle = True
        self.assertTrue(self.backend.playback.shuffle.get())
        result = self.mpris.Set(mpris.PLAYER_IFACE, 'Shuffle', False)
        self.assertFalse(self.backend.playback.shuffle.get())

    def test_get_volume_should_return_volume_between_zero_and_one(self):
        self.mixer.volume = 0
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'Volume')
        self.assertEquals(result, 0)

        self.mixer.volume = 50
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'Volume')
        self.assertEquals(result, 0.5)

        self.mixer.volume = 100
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'Volume')
        self.assertEquals(result, 1)

    def test_set_volume_is_ignored_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        self.mixer.volume = 0
        self.mpris.Set(mpris.PLAYER_IFACE, 'Volume', 1.0)
        self.assertEquals(self.mixer.volume.get(), 0)

    def test_set_volume_to_one_should_set_mixer_volume_to_100(self):
        self.mpris.Set(mpris.PLAYER_IFACE, 'Volume', 1.0)
        self.assertEquals(self.mixer.volume.get(), 100)

    def test_set_volume_to_anything_above_one_should_set_mixer_volume_to_100(self):
        self.mpris.Set(mpris.PLAYER_IFACE, 'Volume', 2.0)
        self.assertEquals(self.mixer.volume.get(), 100)

    def test_set_volume_to_anything_not_a_number_does_not_change_volume(self):
        self.mixer.volume = 10
        self.mpris.Set(mpris.PLAYER_IFACE, 'Volume', None)
        self.assertEquals(self.mixer.volume.get(), 10)

    def test_get_position_returns_time_position_in_microseconds(self):
        self.backend.current_playlist.append([Track(uri='a', length=40000)])
        self.backend.playback.play()
        self.backend.playback.seek(10000)
        result_in_microseconds = self.mpris.Get(mpris.PLAYER_IFACE, 'Position')
        result_in_milliseconds = result_in_microseconds // 1000
        self.assert_(result_in_milliseconds >= 10000)

    def test_get_position_when_no_current_track_should_be_zero(self):
        result_in_microseconds = self.mpris.Get(mpris.PLAYER_IFACE, 'Position')
        result_in_milliseconds = result_in_microseconds // 1000
        self.assertEquals(result_in_milliseconds, 0)

    def test_get_minimum_rate_is_one_or_less(self):
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'MinimumRate')
        self.assert_(result <= 1.0)

    def test_get_maximum_rate_is_one_or_more(self):
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'MaximumRate')
        self.assert_(result >= 1.0)

    def test_can_play_is_true_if_can_control_and_current_track(self):
        self.mpris.get_CanControl = lambda *_: True
        self.backend.current_playlist.append([Track(uri='a')])
        self.backend.playback.play()
        self.assertTrue(self.backend.playback.current_track.get())
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'CanPlay')
        self.assertTrue(result)

    def test_can_play_is_false_if_no_current_track(self):
        self.mpris.get_CanControl = lambda *_: True
        self.assertFalse(self.backend.playback.current_track.get())
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'CanPlay')
        self.assertFalse(result)

    def test_can_play_if_false_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'CanPlay')
        self.assertFalse(result)

    def test_can_pause_is_true_if_can_control_and_track_can_be_paused(self):
        self.mpris.get_CanControl = lambda *_: True
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'CanPause')
        self.assertTrue(result)

    def test_can_pause_if_false_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'CanPause')
        self.assertFalse(result)

    def test_can_seek_is_true_if_can_control_is_true(self):
        self.mpris.get_CanControl = lambda *_: True
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'CanSeek')
        self.assertTrue(result)

    def test_can_seek_is_false_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'CanSeek')
        self.assertFalse(result)

    def test_can_control_is_true(self):
        result = self.mpris.Get(mpris.PLAYER_IFACE, 'CanControl')
        self.assertTrue(result)

    def test_next_when_playing_should_skip_to_next_track_and_keep_playing(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.assertEquals(self.backend.playback.current_track.get().uri, 'a')
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.mpris.Next()
        self.assertEquals(self.backend.playback.current_track.get().uri, 'b')
        self.assertEquals(self.backend.playback.state.get(), PLAYING)

    def test_next_when_at_end_of_list_should_stop_playback(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.backend.playback.next()
        self.assertEquals(self.backend.playback.current_track.get().uri, 'b')
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.mpris.Next()
        self.assertEquals(self.backend.playback.state.get(), STOPPED)

    def test_next_when_paused_should_skip_to_next_track_and_stay_paused(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.backend.playback.pause()
        self.assertEquals(self.backend.playback.current_track.get().uri, 'a')
        self.assertEquals(self.backend.playback.state.get(), PAUSED)
        self.mpris.Next()
        self.assertEquals(self.backend.playback.current_track.get().uri, 'b')
        self.assertEquals(self.backend.playback.state.get(), PAUSED)

    def test_next_when_stopped_should_skip_to_next_track_and_stay_stopped(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.backend.playback.stop()
        self.assertEquals(self.backend.playback.current_track.get().uri, 'a')
        self.assertEquals(self.backend.playback.state.get(), STOPPED)
        self.mpris.Next()
        self.assertEquals(self.backend.playback.current_track.get().uri, 'b')
        self.assertEquals(self.backend.playback.state.get(), STOPPED)

    def test_previous_when_playing_should_skip_to_prev_track_and_keep_playing(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.backend.playback.next()
        self.assertEquals(self.backend.playback.current_track.get().uri, 'b')
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.mpris.Previous()
        self.assertEquals(self.backend.playback.current_track.get().uri, 'a')
        self.assertEquals(self.backend.playback.state.get(), PLAYING)

    def test_previous_when_at_start_of_list_should_stop_playback(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.assertEquals(self.backend.playback.current_track.get().uri, 'a')
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.mpris.Previous()
        self.assertEquals(self.backend.playback.state.get(), STOPPED)

    def test_previous_when_paused_should_skip_to_previous_track_and_stay_paused(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.backend.playback.next()
        self.backend.playback.pause()
        self.assertEquals(self.backend.playback.current_track.get().uri, 'b')
        self.assertEquals(self.backend.playback.state.get(), PAUSED)
        self.mpris.Previous()
        self.assertEquals(self.backend.playback.current_track.get().uri, 'a')
        self.assertEquals(self.backend.playback.state.get(), PAUSED)

    def test_previous_when_stopped_should_skip_to_previous_track_and_stay_stopped(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.backend.playback.next()
        self.backend.playback.stop()
        self.assertEquals(self.backend.playback.current_track.get().uri, 'b')
        self.assertEquals(self.backend.playback.state.get(), STOPPED)
        self.mpris.Previous()
        self.assertEquals(self.backend.playback.current_track.get().uri, 'a')
        self.assertEquals(self.backend.playback.state.get(), STOPPED)

    def test_pause_is_ignored_if_can_pause_is_false(self):
        self.mpris.get_CanPause = lambda *_: False
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.mpris.Pause()
        self.assertEquals(self.backend.playback.state.get(), PLAYING)

    def test_pause_when_playing_should_pause_playback(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.mpris.Pause()
        self.assertEquals(self.backend.playback.state.get(), PAUSED)

    def test_pause_when_paused_has_no_effect(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.backend.playback.pause()
        self.assertEquals(self.backend.playback.state.get(), PAUSED)
        self.mpris.Pause()
        self.assertEquals(self.backend.playback.state.get(), PAUSED)

    def test_playpause_is_ignored_if_can_pause_is_false(self):
        self.mpris.get_CanPause = lambda *_: False
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.mpris.PlayPause()
        self.assertEquals(self.backend.playback.state.get(), PLAYING)

    def test_playpause_when_playing_should_pause_playback(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.mpris.PlayPause()
        self.assertEquals(self.backend.playback.state.get(), PAUSED)

    def test_playpause_when_paused_should_resume_playback(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.backend.playback.pause()

        self.assertEquals(self.backend.playback.state.get(), PAUSED)
        at_pause = self.backend.playback.time_position.get()
        self.assert_(at_pause >= 0)

        self.mpris.PlayPause()

        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        after_pause = self.backend.playback.time_position.get()
        self.assert_(after_pause >= at_pause)

    def test_playpause_when_stopped_should_start_playback(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.assertEquals(self.backend.playback.state.get(), STOPPED)
        self.mpris.PlayPause()
        self.assertEquals(self.backend.playback.state.get(), PLAYING)

    def test_stop_is_ignored_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.mpris.Stop()
        self.assertEquals(self.backend.playback.state.get(), PLAYING)

    def test_stop_when_playing_should_stop_playback(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.mpris.Stop()
        self.assertEquals(self.backend.playback.state.get(), STOPPED)

    def test_stop_when_paused_should_stop_playback(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.backend.playback.pause()
        self.assertEquals(self.backend.playback.state.get(), PAUSED)
        self.mpris.Stop()
        self.assertEquals(self.backend.playback.state.get(), STOPPED)

    def test_play_when_stopped_starts_playback(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.assertEquals(self.backend.playback.state.get(), STOPPED)
        self.mpris.Play()
        self.assertEquals(self.backend.playback.state.get(), PLAYING)

    def test_play_after_pause_resumes_from_same_position(self):
        self.backend.current_playlist.append([Track(uri='a', length=40000)])
        self.backend.playback.play()

        before_pause = self.backend.playback.time_position.get()
        self.assert_(before_pause >= 0)

        self.mpris.Pause()
        self.assertEquals(self.backend.playback.state.get(), PAUSED)
        at_pause = self.backend.playback.time_position.get()
        self.assert_(at_pause >= before_pause)

        self.mpris.Play()
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        after_pause = self.backend.playback.time_position.get()
        self.assert_(after_pause >= at_pause)

    def test_play_when_there_is_no_track_has_no_effect(self):
        self.backend.current_playlist.clear()
        self.assertEquals(self.backend.playback.state.get(), STOPPED)
        self.mpris.Play()
        self.assertEquals(self.backend.playback.state.get(), STOPPED)

    def test_seek_is_ignored_if_can_seek_is_false(self):
        self.mpris.get_CanSeek = lambda *_: False
        self.backend.current_playlist.append([Track(uri='a', length=40000)])
        self.backend.playback.play()

        before_seek = self.backend.playback.time_position.get()
        self.assert_(before_seek >= 0)

        milliseconds_to_seek = 10000
        microseconds_to_seek = milliseconds_to_seek * 1000

        self.mpris.Seek(microseconds_to_seek)

        after_seek = self.backend.playback.time_position.get()
        self.assert_(before_seek <= after_seek < (
            before_seek + milliseconds_to_seek))

    def test_seek_seeks_given_microseconds_forward_in_the_current_track(self):
        self.backend.current_playlist.append([Track(uri='a', length=40000)])
        self.backend.playback.play()

        before_seek = self.backend.playback.time_position.get()
        self.assert_(before_seek >= 0)

        milliseconds_to_seek = 10000
        microseconds_to_seek = milliseconds_to_seek * 1000

        self.mpris.Seek(microseconds_to_seek)

        self.assertEquals(self.backend.playback.state.get(), PLAYING)

        after_seek = self.backend.playback.time_position.get()
        self.assert_(after_seek >= (before_seek + milliseconds_to_seek))

    def test_seek_seeks_given_microseconds_backward_if_negative(self):
        self.backend.current_playlist.append([Track(uri='a', length=40000)])
        self.backend.playback.play()
        self.backend.playback.seek(20000)

        before_seek = self.backend.playback.time_position.get()
        self.assert_(before_seek >= 20000)

        milliseconds_to_seek = -10000
        microseconds_to_seek = milliseconds_to_seek * 1000

        self.mpris.Seek(microseconds_to_seek)

        self.assertEquals(self.backend.playback.state.get(), PLAYING)

        after_seek = self.backend.playback.time_position.get()
        self.assert_(after_seek >= (before_seek + milliseconds_to_seek))
        self.assert_(after_seek < before_seek)

    def test_seek_seeks_to_start_of_track_if_new_position_is_negative(self):
        self.backend.current_playlist.append([Track(uri='a', length=40000)])
        self.backend.playback.play()
        self.backend.playback.seek(20000)

        before_seek = self.backend.playback.time_position.get()
        self.assert_(before_seek >= 20000)

        milliseconds_to_seek = -30000
        microseconds_to_seek = milliseconds_to_seek * 1000

        self.mpris.Seek(microseconds_to_seek)

        self.assertEquals(self.backend.playback.state.get(), PLAYING)

        after_seek = self.backend.playback.time_position.get()
        self.assert_(after_seek >= (before_seek + milliseconds_to_seek))
        self.assert_(after_seek < before_seek)
        self.assert_(after_seek >= 0)

    def test_seek_skips_to_next_track_if_new_position_larger_than_track_length(self):
        self.backend.current_playlist.append([Track(uri='a', length=40000),
            Track(uri='b')])
        self.backend.playback.play()
        self.backend.playback.seek(20000)

        before_seek = self.backend.playback.time_position.get()
        self.assert_(before_seek >= 20000)
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.assertEquals(self.backend.playback.current_track.get().uri, 'a')

        milliseconds_to_seek = 50000
        microseconds_to_seek = milliseconds_to_seek * 1000

        self.mpris.Seek(microseconds_to_seek)

        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.assertEquals(self.backend.playback.current_track.get().uri, 'b')

        after_seek = self.backend.playback.time_position.get()
        self.assert_(after_seek >= 0)
        self.assert_(after_seek < before_seek)

    def test_set_position_is_ignored_if_can_seek_is_false(self):
        self.mpris.get_CanSeek = lambda *_: False
        self.backend.current_playlist.append([Track(uri='a', length=40000)])
        self.backend.playback.play()

        before_set_position = self.backend.playback.time_position.get()
        self.assert_(before_set_position <= 5000)

        track_id = 'a'

        position_to_set_in_milliseconds = 20000
        position_to_set_in_microseconds = position_to_set_in_milliseconds * 1000

        self.mpris.SetPosition(track_id, position_to_set_in_microseconds)

        after_set_position = self.backend.playback.time_position.get()
        self.assert_(before_set_position <= after_set_position <
            position_to_set_in_milliseconds)

    def test_set_position_sets_the_current_track_position_in_microsecs(self):
        self.backend.current_playlist.append([Track(uri='a', length=40000)])
        self.backend.playback.play()

        before_set_position = self.backend.playback.time_position.get()
        self.assert_(before_set_position <= 5000)
        self.assertEquals(self.backend.playback.state.get(), PLAYING)

        track_id = 'a'

        position_to_set_in_milliseconds = 20000
        position_to_set_in_microseconds = position_to_set_in_milliseconds * 1000

        self.mpris.SetPosition(track_id, position_to_set_in_microseconds)

        self.assertEquals(self.backend.playback.state.get(), PLAYING)

        after_set_position = self.backend.playback.time_position.get()
        self.assert_(after_set_position >= position_to_set_in_milliseconds)

    def test_set_position_does_nothing_if_the_position_is_negative(self):
        self.backend.current_playlist.append([Track(uri='a', length=40000)])
        self.backend.playback.play()
        self.backend.playback.seek(20000)

        before_set_position = self.backend.playback.time_position.get()
        self.assert_(before_set_position >= 20000)
        self.assert_(before_set_position <= 25000)
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.assertEquals(self.backend.playback.current_track.get().uri, 'a')

        track_id = 'a'

        position_to_set_in_milliseconds = -1000
        position_to_set_in_microseconds = position_to_set_in_milliseconds * 1000

        self.mpris.SetPosition(track_id, position_to_set_in_microseconds)

        after_set_position = self.backend.playback.time_position.get()
        self.assert_(after_set_position >= before_set_position)
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.assertEquals(self.backend.playback.current_track.get().uri, 'a')

    def test_set_position_does_nothing_if_position_is_larger_than_track_length(self):
        self.backend.current_playlist.append([Track(uri='a', length=40000)])
        self.backend.playback.play()
        self.backend.playback.seek(20000)

        before_set_position = self.backend.playback.time_position.get()
        self.assert_(before_set_position >= 20000)
        self.assert_(before_set_position <= 25000)
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.assertEquals(self.backend.playback.current_track.get().uri, 'a')

        track_id = 'a'

        position_to_set_in_milliseconds = 50000
        position_to_set_in_microseconds = position_to_set_in_milliseconds * 1000

        self.mpris.SetPosition(track_id, position_to_set_in_microseconds)

        after_set_position = self.backend.playback.time_position.get()
        self.assert_(after_set_position >= before_set_position)
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.assertEquals(self.backend.playback.current_track.get().uri, 'a')

    def test_set_position_does_nothing_if_track_id_does_not_match_current_track(self):
        self.backend.current_playlist.append([Track(uri='a', length=40000)])
        self.backend.playback.play()
        self.backend.playback.seek(20000)

        before_set_position = self.backend.playback.time_position.get()
        self.assert_(before_set_position >= 20000)
        self.assert_(before_set_position <= 25000)
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.assertEquals(self.backend.playback.current_track.get().uri, 'a')

        track_id = 'b'

        position_to_set_in_milliseconds = 0
        position_to_set_in_microseconds = position_to_set_in_milliseconds * 1000

        self.mpris.SetPosition(track_id, position_to_set_in_microseconds)

        after_set_position = self.backend.playback.time_position.get()
        self.assert_(after_set_position >= before_set_position)
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.assertEquals(self.backend.playback.current_track.get().uri, 'a')

    def test_open_uri_adds_uri_to_current_playlist(self):
        self.backend.library.provider.dummy_library = [
            Track(uri='dummy:/test/uri')]
        self.mpris.OpenUri('dummy:/test/uri')
        self.assertEquals(self.backend.current_playlist.tracks.get()[0].uri,
            'dummy:/test/uri')

    def test_open_uri_starts_playback_of_new_track_if_stopped(self):
        self.backend.library.provider.dummy_library = [
            Track(uri='dummy:/test/uri')]
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.assertEquals(self.backend.playback.state.get(), STOPPED)

        self.mpris.OpenUri('dummy:/test/uri')

        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.assertEquals(self.backend.playback.current_track.get().uri,
            'dummy:/test/uri')

    def test_open_uri_starts_playback_of_new_track_if_paused(self):
        self.backend.library.provider.dummy_library = [
            Track(uri='dummy:/test/uri')]
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.backend.playback.pause()
        self.assertEquals(self.backend.playback.state.get(), PAUSED)
        self.assertEquals(self.backend.playback.current_track.get().uri, 'a')

        self.mpris.OpenUri('dummy:/test/uri')

        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.assertEquals(self.backend.playback.current_track.get().uri,
            'dummy:/test/uri')

    def test_open_uri_starts_playback_of_new_track_if_playing(self):
        self.backend.library.provider.dummy_library = [
            Track(uri='dummy:/test/uri')]
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.assertEquals(self.backend.playback.current_track.get().uri, 'a')

        self.mpris.OpenUri('dummy:/test/uri')

        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.assertEquals(self.backend.playback.current_track.get().uri,
            'dummy:/test/uri')
