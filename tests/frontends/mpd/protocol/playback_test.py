from mopidy.backends import base as backend
from mopidy.models import Track

from tests import unittest
from tests.frontends.mpd import protocol

PAUSED = backend.PlaybackController.PAUSED
PLAYING = backend.PlaybackController.PLAYING
STOPPED = backend.PlaybackController.STOPPED


class PlaybackOptionsHandlerTest(protocol.BaseTestCase):
    def test_consume_off(self):
        self.sendRequest(u'consume "0"')
        self.assertFalse(self.backend.playback.consume.get())
        self.assertInResponse(u'OK')

    def test_consume_off_without_quotes(self):
        self.sendRequest(u'consume 0')
        self.assertFalse(self.backend.playback.consume.get())
        self.assertInResponse(u'OK')

    def test_consume_on(self):
        self.sendRequest(u'consume "1"')
        self.assertTrue(self.backend.playback.consume.get())
        self.assertInResponse(u'OK')

    def test_consume_on_without_quotes(self):
        self.sendRequest(u'consume 1')
        self.assertTrue(self.backend.playback.consume.get())
        self.assertInResponse(u'OK')

    def test_crossfade(self):
        self.sendRequest(u'crossfade "10"')
        self.assertInResponse(u'ACK [0@0] {} Not implemented')

    def test_random_off(self):
        self.sendRequest(u'random "0"')
        self.assertFalse(self.backend.playback.random.get())
        self.assertInResponse(u'OK')

    def test_random_off_without_quotes(self):
        self.sendRequest(u'random 0')
        self.assertFalse(self.backend.playback.random.get())
        self.assertInResponse(u'OK')

    def test_random_on(self):
        self.sendRequest(u'random "1"')
        self.assertTrue(self.backend.playback.random.get())
        self.assertInResponse(u'OK')

    def test_random_on_without_quotes(self):
        self.sendRequest(u'random 1')
        self.assertTrue(self.backend.playback.random.get())
        self.assertInResponse(u'OK')

    def test_repeat_off(self):
        self.sendRequest(u'repeat "0"')
        self.assertFalse(self.backend.playback.repeat.get())
        self.assertInResponse(u'OK')

    def test_repeat_off_without_quotes(self):
        self.sendRequest(u'repeat 0')
        self.assertFalse(self.backend.playback.repeat.get())
        self.assertInResponse(u'OK')

    def test_repeat_on(self):
        self.sendRequest(u'repeat "1"')
        self.assertTrue(self.backend.playback.repeat.get())
        self.assertInResponse(u'OK')

    def test_repeat_on_without_quotes(self):
        self.sendRequest(u'repeat 1')
        self.assertTrue(self.backend.playback.repeat.get())
        self.assertInResponse(u'OK')

    def test_setvol_below_min(self):
        self.sendRequest(u'setvol "-10"')
        self.assertEqual(0, self.mixer.volume.get())
        self.assertInResponse(u'OK')

    def test_setvol_min(self):
        self.sendRequest(u'setvol "0"')
        self.assertEqual(0, self.mixer.volume.get())
        self.assertInResponse(u'OK')

    def test_setvol_middle(self):
        self.sendRequest(u'setvol "50"')
        self.assertEqual(50, self.mixer.volume.get())
        self.assertInResponse(u'OK')

    def test_setvol_max(self):
        self.sendRequest(u'setvol "100"')
        self.assertEqual(100, self.mixer.volume.get())
        self.assertInResponse(u'OK')

    def test_setvol_above_max(self):
        self.sendRequest(u'setvol "110"')
        self.assertEqual(100, self.mixer.volume.get())
        self.assertInResponse(u'OK')

    def test_setvol_plus_is_ignored(self):
        self.sendRequest(u'setvol "+10"')
        self.assertEqual(10, self.mixer.volume.get())
        self.assertInResponse(u'OK')

    def test_setvol_without_quotes(self):
        self.sendRequest(u'setvol 50')
        self.assertEqual(50, self.mixer.volume.get())
        self.assertInResponse(u'OK')

    def test_single_off(self):
        self.sendRequest(u'single "0"')
        self.assertFalse(self.backend.playback.single.get())
        self.assertInResponse(u'OK')

    def test_single_off_without_quotes(self):
        self.sendRequest(u'single 0')
        self.assertFalse(self.backend.playback.single.get())
        self.assertInResponse(u'OK')

    def test_single_on(self):
        self.sendRequest(u'single "1"')
        self.assertTrue(self.backend.playback.single.get())
        self.assertInResponse(u'OK')

    def test_single_on_without_quotes(self):
        self.sendRequest(u'single 1')
        self.assertTrue(self.backend.playback.single.get())
        self.assertInResponse(u'OK')

    def test_replay_gain_mode_off(self):
        self.sendRequest(u'replay_gain_mode "off"')
        self.assertInResponse(u'ACK [0@0] {} Not implemented')

    def test_replay_gain_mode_track(self):
        self.sendRequest(u'replay_gain_mode "track"')
        self.assertInResponse(u'ACK [0@0] {} Not implemented')

    def test_replay_gain_mode_album(self):
        self.sendRequest(u'replay_gain_mode "album"')
        self.assertInResponse(u'ACK [0@0] {} Not implemented')

    def test_replay_gain_status_default(self):
        self.sendRequest(u'replay_gain_status')
        self.assertInResponse(u'OK')
        self.assertInResponse(u'off')

    @unittest.SkipTest
    def test_replay_gain_status_off(self):
        pass

    @unittest.SkipTest
    def test_replay_gain_status_track(self):
        pass

    @unittest.SkipTest
    def test_replay_gain_status_album(self):
        pass


class PlaybackControlHandlerTest(protocol.BaseTestCase):
    def test_next(self):
        self.sendRequest(u'next')
        self.assertInResponse(u'OK')

    def test_pause_off(self):
        self.backend.current_playlist.append([Track()])

        self.sendRequest(u'play "0"')
        self.sendRequest(u'pause "1"')
        self.sendRequest(u'pause "0"')
        self.assertEqual(PLAYING, self.backend.playback.state.get())
        self.assertInResponse(u'OK')

    def test_pause_on(self):
        self.backend.current_playlist.append([Track()])

        self.sendRequest(u'play "0"')
        self.sendRequest(u'pause "1"')
        self.assertEqual(PAUSED, self.backend.playback.state.get())
        self.assertInResponse(u'OK')

    def test_pause_toggle(self):
        self.backend.current_playlist.append([Track()])

        self.sendRequest(u'play "0"')
        self.assertEqual(PLAYING, self.backend.playback.state.get())
        self.assertInResponse(u'OK')

        self.sendRequest(u'pause')
        self.assertEqual(PAUSED, self.backend.playback.state.get())
        self.assertInResponse(u'OK')

        self.sendRequest(u'pause')
        self.assertEqual(PLAYING, self.backend.playback.state.get())
        self.assertInResponse(u'OK')

    def test_play_without_pos(self):
        self.backend.current_playlist.append([Track()])
        self.backend.playback.state = PAUSED

        self.sendRequest(u'play')
        self.assertEqual(PLAYING, self.backend.playback.state.get())
        self.assertInResponse(u'OK')

    def test_play_with_pos(self):
        self.backend.current_playlist.append([Track()])

        self.sendRequest(u'play "0"')
        self.assertEqual(PLAYING, self.backend.playback.state.get())
        self.assertInResponse(u'OK')

    def test_play_with_pos_without_quotes(self):
        self.backend.current_playlist.append([Track()])

        self.sendRequest(u'play 0')
        self.assertEqual(PLAYING, self.backend.playback.state.get())
        self.assertInResponse(u'OK')

    def test_play_with_pos_out_of_bounds(self):
        self.backend.current_playlist.append([])

        self.sendRequest(u'play "0"')
        self.assertEqual(STOPPED, self.backend.playback.state.get())
        self.assertInResponse(u'ACK [2@0] {play} Bad song index')

    def test_play_minus_one_plays_first_in_playlist_if_no_current_track(self):
        self.assertEqual(self.backend.playback.current_track.get(), None)
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])

        self.sendRequest(u'play "-1"')
        self.assertEqual(PLAYING, self.backend.playback.state.get())
        self.assertEqual('a', self.backend.playback.current_track.get().uri)
        self.assertInResponse(u'OK')

    def test_play_minus_one_plays_current_track_if_current_track_is_set(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.assertEqual(self.backend.playback.current_track.get(), None)
        self.backend.playback.play()
        self.backend.playback.next()
        self.backend.playback.stop()
        self.assertNotEqual(self.backend.playback.current_track.get(), None)

        self.sendRequest(u'play "-1"')
        self.assertEqual(PLAYING, self.backend.playback.state.get())
        self.assertEqual('b', self.backend.playback.current_track.get().uri)
        self.assertInResponse(u'OK')

    def test_play_minus_one_on_empty_playlist_does_not_ack(self):
        self.backend.current_playlist.clear()

        self.sendRequest(u'play "-1"')
        self.assertEqual(STOPPED, self.backend.playback.state.get())
        self.assertEqual(None, self.backend.playback.current_track.get())
        self.assertInResponse(u'OK')

    def test_play_minus_is_ignored_if_playing(self):
        self.backend.current_playlist.append([Track(length=40000)])
        self.backend.playback.seek(30000)
        self.assert_(self.backend.playback.time_position.get() >= 30000)
        self.assertEquals(PLAYING, self.backend.playback.state.get())

        self.sendRequest(u'play "-1"')
        self.assertEqual(PLAYING, self.backend.playback.state.get())
        self.assert_(self.backend.playback.time_position.get() >= 30000)
        self.assertInResponse(u'OK')

    def test_play_minus_one_resumes_if_paused(self):
        self.backend.current_playlist.append([Track(length=40000)])
        self.backend.playback.seek(30000)
        self.assert_(self.backend.playback.time_position.get() >= 30000)
        self.assertEquals(PLAYING, self.backend.playback.state.get())
        self.backend.playback.pause()
        self.assertEquals(PAUSED, self.backend.playback.state.get())

        self.sendRequest(u'play "-1"')
        self.assertEqual(PLAYING, self.backend.playback.state.get())
        self.assert_(self.backend.playback.time_position.get() >= 30000)
        self.assertInResponse(u'OK')

    def test_playid(self):
        self.backend.current_playlist.append([Track()])

        self.sendRequest(u'playid "0"')
        self.assertEqual(PLAYING, self.backend.playback.state.get())
        self.assertInResponse(u'OK')

    def test_playid_minus_one_plays_first_in_playlist_if_no_current_track(self):
        self.assertEqual(self.backend.playback.current_track.get(), None)
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])

        self.sendRequest(u'playid "-1"')
        self.assertEqual(PLAYING, self.backend.playback.state.get())
        self.assertEqual('a', self.backend.playback.current_track.get().uri)
        self.assertInResponse(u'OK')

    def test_playid_minus_one_plays_current_track_if_current_track_is_set(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.assertEqual(self.backend.playback.current_track.get(), None)
        self.backend.playback.play()
        self.backend.playback.next()
        self.backend.playback.stop()
        self.assertNotEqual(None, self.backend.playback.current_track.get())

        self.sendRequest(u'playid "-1"')
        self.assertEqual(PLAYING, self.backend.playback.state.get())
        self.assertEqual('b', self.backend.playback.current_track.get().uri)
        self.assertInResponse(u'OK')

    def test_playid_minus_one_on_empty_playlist_does_not_ack(self):
        self.backend.current_playlist.clear()

        self.sendRequest(u'playid "-1"')
        self.assertEqual(STOPPED, self.backend.playback.state.get())
        self.assertEqual(None, self.backend.playback.current_track.get())
        self.assertInResponse(u'OK')

    def test_playid_minus_is_ignored_if_playing(self):
        self.backend.current_playlist.append([Track(length=40000)])
        self.backend.playback.seek(30000)
        self.assert_(self.backend.playback.time_position.get() >= 30000)
        self.assertEquals(PLAYING, self.backend.playback.state.get())

        self.sendRequest(u'playid "-1"')
        self.assertEqual(PLAYING, self.backend.playback.state.get())
        self.assert_(self.backend.playback.time_position.get() >= 30000)
        self.assertInResponse(u'OK')

    def test_playid_minus_one_resumes_if_paused(self):
        self.backend.current_playlist.append([Track(length=40000)])
        self.backend.playback.seek(30000)
        self.assert_(self.backend.playback.time_position.get() >= 30000)
        self.assertEquals(PLAYING, self.backend.playback.state.get())
        self.backend.playback.pause()
        self.assertEquals(PAUSED, self.backend.playback.state.get())

        self.sendRequest(u'playid "-1"')
        self.assertEqual(PLAYING, self.backend.playback.state.get())
        self.assert_(self.backend.playback.time_position.get() >= 30000)
        self.assertInResponse(u'OK')

    def test_playid_which_does_not_exist(self):
        self.backend.current_playlist.append([Track()])

        self.sendRequest(u'playid "12345"')
        self.assertInResponse(u'ACK [50@0] {playid} No such song')

    def test_previous(self):
        self.sendRequest(u'previous')
        self.assertInResponse(u'OK')

    def test_seek(self):
        self.backend.current_playlist.append([Track(length=40000)])

        self.sendRequest(u'seek "0"')
        self.sendRequest(u'seek "0" "30"')
        self.assert_(self.backend.playback.time_position >= 30000)
        self.assertInResponse(u'OK')

    def test_seek_with_songpos(self):
        seek_track = Track(uri='2', length=40000)
        self.backend.current_playlist.append(
            [Track(uri='1', length=40000), seek_track])

        self.sendRequest(u'seek "1" "30"')
        self.assertEqual(self.backend.playback.current_track.get(), seek_track)
        self.assertInResponse(u'OK')

    def test_seek_without_quotes(self):
        self.backend.current_playlist.append([Track(length=40000)])

        self.sendRequest(u'seek 0')
        self.sendRequest(u'seek 0 30')
        self.assert_(self.backend.playback.time_position.get() >= 30000)
        self.assertInResponse(u'OK')

    def test_seekid(self):
        self.backend.current_playlist.append([Track(length=40000)])
        self.sendRequest(u'seekid "0" "30"')
        self.assert_(self.backend.playback.time_position.get() >= 30000)
        self.assertInResponse(u'OK')

    def test_seekid_with_cpid(self):
        seek_track = Track(uri='2', length=40000)
        self.backend.current_playlist.append(
            [Track(length=40000), seek_track])

        self.sendRequest(u'seekid "1" "30"')
        self.assertEqual(1, self.backend.playback.current_cpid.get())
        self.assertEqual(seek_track, self.backend.playback.current_track.get())
        self.assertInResponse(u'OK')

    def test_stop(self):
        self.sendRequest(u'stop')
        self.assertEqual(STOPPED, self.backend.playback.state.get())
        self.assertInResponse(u'OK')
