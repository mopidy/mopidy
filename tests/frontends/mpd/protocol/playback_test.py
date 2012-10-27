from mopidy.core import PlaybackState
from mopidy.models import Track

from tests import unittest
from tests.frontends.mpd import protocol


PAUSED = PlaybackState.PAUSED
PLAYING = PlaybackState.PLAYING
STOPPED = PlaybackState.STOPPED


class PlaybackOptionsHandlerTest(protocol.BaseTestCase):
    def test_consume_off(self):
        self.sendRequest(u'consume "0"')
        self.assertFalse(self.core.playback.consume.get())
        self.assertInResponse(u'OK')

    def test_consume_off_without_quotes(self):
        self.sendRequest(u'consume 0')
        self.assertFalse(self.core.playback.consume.get())
        self.assertInResponse(u'OK')

    def test_consume_on(self):
        self.sendRequest(u'consume "1"')
        self.assertTrue(self.core.playback.consume.get())
        self.assertInResponse(u'OK')

    def test_consume_on_without_quotes(self):
        self.sendRequest(u'consume 1')
        self.assertTrue(self.core.playback.consume.get())
        self.assertInResponse(u'OK')

    def test_crossfade(self):
        self.sendRequest(u'crossfade "10"')
        self.assertInResponse(u'ACK [0@0] {} Not implemented')

    def test_random_off(self):
        self.sendRequest(u'random "0"')
        self.assertFalse(self.core.playback.random.get())
        self.assertInResponse(u'OK')

    def test_random_off_without_quotes(self):
        self.sendRequest(u'random 0')
        self.assertFalse(self.core.playback.random.get())
        self.assertInResponse(u'OK')

    def test_random_on(self):
        self.sendRequest(u'random "1"')
        self.assertTrue(self.core.playback.random.get())
        self.assertInResponse(u'OK')

    def test_random_on_without_quotes(self):
        self.sendRequest(u'random 1')
        self.assertTrue(self.core.playback.random.get())
        self.assertInResponse(u'OK')

    def test_repeat_off(self):
        self.sendRequest(u'repeat "0"')
        self.assertFalse(self.core.playback.repeat.get())
        self.assertInResponse(u'OK')

    def test_repeat_off_without_quotes(self):
        self.sendRequest(u'repeat 0')
        self.assertFalse(self.core.playback.repeat.get())
        self.assertInResponse(u'OK')

    def test_repeat_on(self):
        self.sendRequest(u'repeat "1"')
        self.assertTrue(self.core.playback.repeat.get())
        self.assertInResponse(u'OK')

    def test_repeat_on_without_quotes(self):
        self.sendRequest(u'repeat 1')
        self.assertTrue(self.core.playback.repeat.get())
        self.assertInResponse(u'OK')

    def test_setvol_below_min(self):
        self.sendRequest(u'setvol "-10"')
        self.assertEqual(0, self.core.playback.volume.get())
        self.assertInResponse(u'OK')

    def test_setvol_min(self):
        self.sendRequest(u'setvol "0"')
        self.assertEqual(0, self.core.playback.volume.get())
        self.assertInResponse(u'OK')

    def test_setvol_middle(self):
        self.sendRequest(u'setvol "50"')
        self.assertEqual(50, self.core.playback.volume.get())
        self.assertInResponse(u'OK')

    def test_setvol_max(self):
        self.sendRequest(u'setvol "100"')
        self.assertEqual(100, self.core.playback.volume.get())
        self.assertInResponse(u'OK')

    def test_setvol_above_max(self):
        self.sendRequest(u'setvol "110"')
        self.assertEqual(100, self.core.playback.volume.get())
        self.assertInResponse(u'OK')

    def test_setvol_plus_is_ignored(self):
        self.sendRequest(u'setvol "+10"')
        self.assertEqual(10, self.core.playback.volume.get())
        self.assertInResponse(u'OK')

    def test_setvol_without_quotes(self):
        self.sendRequest(u'setvol 50')
        self.assertEqual(50, self.core.playback.volume.get())
        self.assertInResponse(u'OK')

    def test_single_off(self):
        self.sendRequest(u'single "0"')
        self.assertFalse(self.core.playback.single.get())
        self.assertInResponse(u'OK')

    def test_single_off_without_quotes(self):
        self.sendRequest(u'single 0')
        self.assertFalse(self.core.playback.single.get())
        self.assertInResponse(u'OK')

    def test_single_on(self):
        self.sendRequest(u'single "1"')
        self.assertTrue(self.core.playback.single.get())
        self.assertInResponse(u'OK')

    def test_single_on_without_quotes(self):
        self.sendRequest(u'single 1')
        self.assertTrue(self.core.playback.single.get())
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
        self.core.current_playlist.append([Track(uri='dummy:a')])

        self.sendRequest(u'play "0"')
        self.sendRequest(u'pause "1"')
        self.sendRequest(u'pause "0"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse(u'OK')

    def test_pause_on(self):
        self.core.current_playlist.append([Track(uri='dummy:a')])

        self.sendRequest(u'play "0"')
        self.sendRequest(u'pause "1"')
        self.assertEqual(PAUSED, self.core.playback.state.get())
        self.assertInResponse(u'OK')

    def test_pause_toggle(self):
        self.core.current_playlist.append([Track(uri='dummy:a')])

        self.sendRequest(u'play "0"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse(u'OK')

        self.sendRequest(u'pause')
        self.assertEqual(PAUSED, self.core.playback.state.get())
        self.assertInResponse(u'OK')

        self.sendRequest(u'pause')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse(u'OK')

    def test_play_without_pos(self):
        self.core.current_playlist.append([Track(uri='dummy:a')])

        self.sendRequest(u'play')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse(u'OK')

    def test_play_with_pos(self):
        self.core.current_playlist.append([Track(uri='dummy:a')])

        self.sendRequest(u'play "0"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse(u'OK')

    def test_play_with_pos_without_quotes(self):
        self.core.current_playlist.append([Track(uri='dummy:a')])

        self.sendRequest(u'play 0')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse(u'OK')

    def test_play_with_pos_out_of_bounds(self):
        self.core.current_playlist.append([])

        self.sendRequest(u'play "0"')
        self.assertEqual(STOPPED, self.core.playback.state.get())
        self.assertInResponse(u'ACK [2@0] {play} Bad song index')

    def test_play_minus_one_plays_first_in_playlist_if_no_current_track(self):
        self.assertEqual(self.core.playback.current_track.get(), None)
        self.core.current_playlist.append([
            Track(uri='dummy:a'),
            Track(uri='dummy:b'),
        ])

        self.sendRequest(u'play "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertEqual('dummy:a',
            self.core.playback.current_track.get().uri)
        self.assertInResponse(u'OK')

    def test_play_minus_one_plays_current_track_if_current_track_is_set(self):
        self.core.current_playlist.append([
            Track(uri='dummy:a'),
            Track(uri='dummy:b'),
        ])
        self.assertEqual(self.core.playback.current_track.get(), None)
        self.core.playback.play()
        self.core.playback.next()
        self.core.playback.stop()
        self.assertNotEqual(self.core.playback.current_track.get(), None)

        self.sendRequest(u'play "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertEqual('dummy:b',
            self.core.playback.current_track.get().uri)
        self.assertInResponse(u'OK')

    def test_play_minus_one_on_empty_playlist_does_not_ack(self):
        self.core.current_playlist.clear()

        self.sendRequest(u'play "-1"')
        self.assertEqual(STOPPED, self.core.playback.state.get())
        self.assertEqual(None, self.core.playback.current_track.get())
        self.assertInResponse(u'OK')

    def test_play_minus_is_ignored_if_playing(self):
        self.core.current_playlist.append([
            Track(uri='dummy:a', length=40000)])
        self.core.playback.seek(30000)
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertEquals(PLAYING, self.core.playback.state.get())

        self.sendRequest(u'play "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse(u'OK')

    def test_play_minus_one_resumes_if_paused(self):
        self.core.current_playlist.append([
            Track(uri='dummy:a', length=40000)])
        self.core.playback.seek(30000)
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertEquals(PLAYING, self.core.playback.state.get())
        self.core.playback.pause()
        self.assertEquals(PAUSED, self.core.playback.state.get())

        self.sendRequest(u'play "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse(u'OK')

    def test_playid(self):
        self.core.current_playlist.append([Track(uri='dummy:a')])

        self.sendRequest(u'playid "0"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse(u'OK')

    def test_playid_without_quotes(self):
        self.core.current_playlist.append([Track(uri='dummy:a')])

        self.sendRequest(u'playid 0')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse(u'OK')

    def test_playid_minus_1_plays_first_in_playlist_if_no_current_track(self):
        self.assertEqual(self.core.playback.current_track.get(), None)
        self.core.current_playlist.append([
            Track(uri='dummy:a'),
            Track(uri='dummy:b'),
        ])

        self.sendRequest(u'playid "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertEqual('dummy:a',
            self.core.playback.current_track.get().uri)
        self.assertInResponse(u'OK')

    def test_playid_minus_1_plays_current_track_if_current_track_is_set(self):
        self.core.current_playlist.append([
            Track(uri='dummy:a'),
            Track(uri='dummy:b'),
        ])
        self.assertEqual(self.core.playback.current_track.get(), None)
        self.core.playback.play()
        self.core.playback.next()
        self.core.playback.stop()
        self.assertNotEqual(None, self.core.playback.current_track.get())

        self.sendRequest(u'playid "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertEqual('dummy:b',
            self.core.playback.current_track.get().uri)
        self.assertInResponse(u'OK')

    def test_playid_minus_one_on_empty_playlist_does_not_ack(self):
        self.core.current_playlist.clear()

        self.sendRequest(u'playid "-1"')
        self.assertEqual(STOPPED, self.core.playback.state.get())
        self.assertEqual(None, self.core.playback.current_track.get())
        self.assertInResponse(u'OK')

    def test_playid_minus_is_ignored_if_playing(self):
        self.core.current_playlist.append([Track(uri='dummy:a', length=40000)])
        self.core.playback.seek(30000)
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertEquals(PLAYING, self.core.playback.state.get())

        self.sendRequest(u'playid "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse(u'OK')

    def test_playid_minus_one_resumes_if_paused(self):
        self.core.current_playlist.append([Track(uri='dummy:a', length=40000)])
        self.core.playback.seek(30000)
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertEquals(PLAYING, self.core.playback.state.get())
        self.core.playback.pause()
        self.assertEquals(PAUSED, self.core.playback.state.get())

        self.sendRequest(u'playid "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse(u'OK')

    def test_playid_which_does_not_exist(self):
        self.core.current_playlist.append([Track(uri='dummy:a')])

        self.sendRequest(u'playid "12345"')
        self.assertInResponse(u'ACK [50@0] {playid} No such song')

    def test_previous(self):
        self.sendRequest(u'previous')
        self.assertInResponse(u'OK')

    def test_seek(self):
        self.core.current_playlist.append([Track(uri='dummy:a', length=40000)])

        self.sendRequest(u'seek "0"')
        self.sendRequest(u'seek "0" "30"')
        self.assertGreaterEqual(self.core.playback.time_position, 30000)
        self.assertInResponse(u'OK')

    def test_seek_with_songpos(self):
        seek_track = Track(uri='dummy:2', length=40000)
        self.core.current_playlist.append(
            [Track(uri='dummy:1', length=40000), seek_track])

        self.sendRequest(u'seek "1" "30"')
        self.assertEqual(self.core.playback.current_track.get(), seek_track)
        self.assertInResponse(u'OK')

    def test_seek_without_quotes(self):
        self.core.current_playlist.append([Track(uri='dummy:a', length=40000)])

        self.sendRequest(u'seek 0')
        self.sendRequest(u'seek 0 30')
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse(u'OK')

    def test_seekid(self):
        self.core.current_playlist.append([Track(uri='dummy:a', length=40000)])
        self.sendRequest(u'seekid "0" "30"')
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse(u'OK')

    def test_seekid_with_cpid(self):
        seek_track = Track(uri='dummy:2', length=40000)
        self.core.current_playlist.append(
            [Track(uri='dummy:1', length=40000), seek_track])

        self.sendRequest(u'seekid "1" "30"')
        self.assertEqual(1, self.core.playback.current_cpid.get())
        self.assertEqual(seek_track, self.core.playback.current_track.get())
        self.assertInResponse(u'OK')

    def test_stop(self):
        self.sendRequest(u'stop')
        self.assertEqual(STOPPED, self.core.playback.state.get())
        self.assertInResponse(u'OK')
