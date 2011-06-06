import mock
import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.backends.base.playback import PlaybackController
from mopidy.frontends import mpris
from mopidy.models import Track

PLAYING = PlaybackController.PLAYING
PAUSED = PlaybackController.PAUSED
STOPPED = PlaybackController.STOPPED

class PlayerInterfaceTest(unittest.TestCase):
    def setUp(self):
        mpris.MprisObject._connect_to_dbus = mock.Mock()
        self.backend = DummyBackend.start().proxy()
        self.mpris = mpris.MprisObject()
        self.mpris._backend = self.backend

    def tearDown(self):
        self.backend.stop()

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

    def test_play_after_pause_resumes_from_same_position(self):
        self.backend.current_playlist.append([Track(uri='a', length=40000)])
        self.backend.playback.play()

        before_pause = self.backend.playback.time_position.get()
        self.assert_(before_pause >= 0)

        self.mpris.Pause()
        at_pause = self.backend.playback.time_position.get()
        self.assert_(at_pause >= before_pause)

        self.mpris.Play()
        after_pause = self.backend.playback.time_position.get()
        self.assert_(after_pause >= at_pause)

    def test_stop_when_playing_should_stop_playback(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.backend.playback.play()
        self.assertEquals(self.backend.playback.state.get(), PLAYING)
        self.mpris.Stop()
        self.assertEquals(self.backend.playback.state.get(), STOPPED)
