from __future__ import unicode_literals

import unittest

from mopidy.core import PlaybackState
from mopidy.models import Track

from tests.frontends.mpd import protocol


PAUSED = PlaybackState.PAUSED
PLAYING = PlaybackState.PLAYING
STOPPED = PlaybackState.STOPPED


class PlaybackOptionsHandlerTest(protocol.BaseTestCase):
    def test_consume_off(self):
        self.sendRequest('consume "0"')
        self.assertFalse(self.core.tracklist.consume.get())
        self.assertInResponse('OK')

    def test_consume_off_without_quotes(self):
        self.sendRequest('consume 0')
        self.assertFalse(self.core.tracklist.consume.get())
        self.assertInResponse('OK')

    def test_consume_on(self):
        self.sendRequest('consume "1"')
        self.assertTrue(self.core.tracklist.consume.get())
        self.assertInResponse('OK')

    def test_consume_on_without_quotes(self):
        self.sendRequest('consume 1')
        self.assertTrue(self.core.tracklist.consume.get())
        self.assertInResponse('OK')

    def test_crossfade(self):
        self.sendRequest('crossfade "10"')
        self.assertInResponse('ACK [0@0] {} Not implemented')

    def test_random_off(self):
        self.sendRequest('random "0"')
        self.assertFalse(self.core.tracklist.random.get())
        self.assertInResponse('OK')

    def test_random_off_without_quotes(self):
        self.sendRequest('random 0')
        self.assertFalse(self.core.tracklist.random.get())
        self.assertInResponse('OK')

    def test_random_on(self):
        self.sendRequest('random "1"')
        self.assertTrue(self.core.tracklist.random.get())
        self.assertInResponse('OK')

    def test_random_on_without_quotes(self):
        self.sendRequest('random 1')
        self.assertTrue(self.core.tracklist.random.get())
        self.assertInResponse('OK')

    def test_repeat_off(self):
        self.sendRequest('repeat "0"')
        self.assertFalse(self.core.tracklist.repeat.get())
        self.assertInResponse('OK')

    def test_repeat_off_without_quotes(self):
        self.sendRequest('repeat 0')
        self.assertFalse(self.core.tracklist.repeat.get())
        self.assertInResponse('OK')

    def test_repeat_on(self):
        self.sendRequest('repeat "1"')
        self.assertTrue(self.core.tracklist.repeat.get())
        self.assertInResponse('OK')

    def test_repeat_on_without_quotes(self):
        self.sendRequest('repeat 1')
        self.assertTrue(self.core.tracklist.repeat.get())
        self.assertInResponse('OK')

    def test_setvol_below_min(self):
        self.sendRequest('setvol "-10"')
        self.assertEqual(0, self.core.playback.volume.get())
        self.assertInResponse('OK')

    def test_setvol_min(self):
        self.sendRequest('setvol "0"')
        self.assertEqual(0, self.core.playback.volume.get())
        self.assertInResponse('OK')

    def test_setvol_middle(self):
        self.sendRequest('setvol "50"')
        self.assertEqual(50, self.core.playback.volume.get())
        self.assertInResponse('OK')

    def test_setvol_max(self):
        self.sendRequest('setvol "100"')
        self.assertEqual(100, self.core.playback.volume.get())
        self.assertInResponse('OK')

    def test_setvol_above_max(self):
        self.sendRequest('setvol "110"')
        self.assertEqual(100, self.core.playback.volume.get())
        self.assertInResponse('OK')

    def test_setvol_plus_is_ignored(self):
        self.sendRequest('setvol "+10"')
        self.assertEqual(10, self.core.playback.volume.get())
        self.assertInResponse('OK')

    def test_setvol_without_quotes(self):
        self.sendRequest('setvol 50')
        self.assertEqual(50, self.core.playback.volume.get())
        self.assertInResponse('OK')

    def test_single_off(self):
        self.sendRequest('single "0"')
        self.assertFalse(self.core.tracklist.single.get())
        self.assertInResponse('OK')

    def test_single_off_without_quotes(self):
        self.sendRequest('single 0')
        self.assertFalse(self.core.tracklist.single.get())
        self.assertInResponse('OK')

    def test_single_on(self):
        self.sendRequest('single "1"')
        self.assertTrue(self.core.tracklist.single.get())
        self.assertInResponse('OK')

    def test_single_on_without_quotes(self):
        self.sendRequest('single 1')
        self.assertTrue(self.core.tracklist.single.get())
        self.assertInResponse('OK')

    def test_replay_gain_mode_off(self):
        self.sendRequest('replay_gain_mode "off"')
        self.assertInResponse('ACK [0@0] {} Not implemented')

    def test_replay_gain_mode_track(self):
        self.sendRequest('replay_gain_mode "track"')
        self.assertInResponse('ACK [0@0] {} Not implemented')

    def test_replay_gain_mode_album(self):
        self.sendRequest('replay_gain_mode "album"')
        self.assertInResponse('ACK [0@0] {} Not implemented')

    def test_replay_gain_status_default(self):
        self.sendRequest('replay_gain_status')
        self.assertInResponse('OK')
        self.assertInResponse('off')

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
        self.sendRequest('next')
        self.assertInResponse('OK')

    def test_pause_off(self):
        self.core.tracklist.add([Track(uri='dummy:a')])

        self.sendRequest('play "0"')
        self.sendRequest('pause "1"')
        self.sendRequest('pause "0"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse('OK')

    def test_pause_on(self):
        self.core.tracklist.add([Track(uri='dummy:a')])

        self.sendRequest('play "0"')
        self.sendRequest('pause "1"')
        self.assertEqual(PAUSED, self.core.playback.state.get())
        self.assertInResponse('OK')

    def test_pause_toggle(self):
        self.core.tracklist.add([Track(uri='dummy:a')])

        self.sendRequest('play "0"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse('OK')

        self.sendRequest('pause')
        self.assertEqual(PAUSED, self.core.playback.state.get())
        self.assertInResponse('OK')

        self.sendRequest('pause')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse('OK')

    def test_play_without_pos(self):
        self.core.tracklist.add([Track(uri='dummy:a')])

        self.sendRequest('play')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse('OK')

    def test_play_with_pos(self):
        self.core.tracklist.add([Track(uri='dummy:a')])

        self.sendRequest('play "0"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse('OK')

    def test_play_with_pos_without_quotes(self):
        self.core.tracklist.add([Track(uri='dummy:a')])

        self.sendRequest('play 0')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse('OK')

    def test_play_with_pos_out_of_bounds(self):
        self.core.tracklist.add([])

        self.sendRequest('play "0"')
        self.assertEqual(STOPPED, self.core.playback.state.get())
        self.assertInResponse('ACK [2@0] {play} Bad song index')

    def test_play_minus_one_plays_first_in_playlist_if_no_current_track(self):
        self.assertEqual(self.core.playback.current_track.get(), None)
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])

        self.sendRequest('play "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertEqual(
            'dummy:a', self.core.playback.current_track.get().uri)
        self.assertInResponse('OK')

    def test_play_minus_one_plays_current_track_if_current_track_is_set(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.assertEqual(self.core.playback.current_track.get(), None)
        self.core.playback.play()
        self.core.playback.next()
        self.core.playback.stop()
        self.assertNotEqual(self.core.playback.current_track.get(), None)

        self.sendRequest('play "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertEqual(
            'dummy:b', self.core.playback.current_track.get().uri)
        self.assertInResponse('OK')

    def test_play_minus_one_on_empty_playlist_does_not_ack(self):
        self.core.tracklist.clear()

        self.sendRequest('play "-1"')
        self.assertEqual(STOPPED, self.core.playback.state.get())
        self.assertEqual(None, self.core.playback.current_track.get())
        self.assertInResponse('OK')

    def test_play_minus_is_ignored_if_playing(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.seek(30000)
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertEquals(PLAYING, self.core.playback.state.get())

        self.sendRequest('play "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse('OK')

    def test_play_minus_one_resumes_if_paused(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.seek(30000)
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertEquals(PLAYING, self.core.playback.state.get())
        self.core.playback.pause()
        self.assertEquals(PAUSED, self.core.playback.state.get())

        self.sendRequest('play "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse('OK')

    def test_playid(self):
        self.core.tracklist.add([Track(uri='dummy:a')])

        self.sendRequest('playid "0"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse('OK')

    def test_playid_without_quotes(self):
        self.core.tracklist.add([Track(uri='dummy:a')])

        self.sendRequest('playid 0')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse('OK')

    def test_playid_minus_1_plays_first_in_playlist_if_no_current_track(self):
        self.assertEqual(self.core.playback.current_track.get(), None)
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])

        self.sendRequest('playid "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertEqual(
            'dummy:a', self.core.playback.current_track.get().uri)
        self.assertInResponse('OK')

    def test_playid_minus_1_plays_current_track_if_current_track_is_set(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.assertEqual(self.core.playback.current_track.get(), None)
        self.core.playback.play()
        self.core.playback.next()
        self.core.playback.stop()
        self.assertNotEqual(None, self.core.playback.current_track.get())

        self.sendRequest('playid "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertEqual(
            'dummy:b', self.core.playback.current_track.get().uri)
        self.assertInResponse('OK')

    def test_playid_minus_one_on_empty_playlist_does_not_ack(self):
        self.core.tracklist.clear()

        self.sendRequest('playid "-1"')
        self.assertEqual(STOPPED, self.core.playback.state.get())
        self.assertEqual(None, self.core.playback.current_track.get())
        self.assertInResponse('OK')

    def test_playid_minus_is_ignored_if_playing(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.seek(30000)
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertEquals(PLAYING, self.core.playback.state.get())

        self.sendRequest('playid "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse('OK')

    def test_playid_minus_one_resumes_if_paused(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.seek(30000)
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertEquals(PLAYING, self.core.playback.state.get())
        self.core.playback.pause()
        self.assertEquals(PAUSED, self.core.playback.state.get())

        self.sendRequest('playid "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse('OK')

    def test_playid_which_does_not_exist(self):
        self.core.tracklist.add([Track(uri='dummy:a')])

        self.sendRequest('playid "12345"')
        self.assertInResponse('ACK [50@0] {playid} No such song')

    def test_previous(self):
        self.sendRequest('previous')
        self.assertInResponse('OK')

    def test_seek_in_current_track(self):
        seek_track = Track(uri='dummy:a', length=40000)
        self.core.tracklist.add([seek_track])
        self.core.playback.play()

        self.sendRequest('seek "0" "30"')

        self.assertEqual(self.core.playback.current_track.get(), seek_track)
        self.assertGreaterEqual(self.core.playback.time_position, 30000)
        self.assertInResponse('OK')

    def test_seek_in_another_track(self):
        seek_track = Track(uri='dummy:b', length=40000)
        self.core.tracklist.add(
            [Track(uri='dummy:a', length=40000), seek_track])
        self.core.playback.play()
        self.assertNotEqual(self.core.playback.current_track.get(), seek_track)

        self.sendRequest('seek "1" "30"')

        self.assertEqual(self.core.playback.current_track.get(), seek_track)
        self.assertInResponse('OK')

    def test_seek_without_quotes(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.play()

        self.sendRequest('seek 0 30')
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse('OK')

    def test_seekid_in_current_track(self):
        seek_track = Track(uri='dummy:a', length=40000)
        self.core.tracklist.add([seek_track])
        self.core.playback.play()

        self.sendRequest('seekid "0" "30"')

        self.assertEqual(self.core.playback.current_track.get(), seek_track)
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse('OK')

    def test_seekid_in_another_track(self):
        seek_track = Track(uri='dummy:b', length=40000)
        self.core.tracklist.add(
            [Track(uri='dummy:a', length=40000), seek_track])
        self.core.playback.play()

        self.sendRequest('seekid "1" "30"')

        self.assertEqual(1, self.core.playback.current_tl_track.get().tlid)
        self.assertEqual(seek_track, self.core.playback.current_track.get())
        self.assertInResponse('OK')

    def test_seekcur_absolute_value(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.play()

        self.sendRequest('seekcur "30"')

        self.assertGreaterEqual(self.core.playback.time_position.get(), 30000)
        self.assertInResponse('OK')

    def test_seekcur_positive_diff(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.play()
        self.core.playback.seek(10000)
        self.assertGreaterEqual(self.core.playback.time_position.get(), 10000)

        self.sendRequest('seekcur "+20"')

        self.assertGreaterEqual(self.core.playback.time_position.get(), 30000)
        self.assertInResponse('OK')

    def test_seekcur_negative_diff(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.play()
        self.core.playback.seek(30000)
        self.assertGreaterEqual(self.core.playback.time_position.get(), 30000)

        self.sendRequest('seekcur "-20"')

        self.assertLessEqual(self.core.playback.time_position.get(), 15000)
        self.assertInResponse('OK')

    def test_stop(self):
        self.sendRequest('stop')
        self.assertEqual(STOPPED, self.core.playback.state.get())
        self.assertInResponse('OK')
