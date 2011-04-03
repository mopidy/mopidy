import unittest

from mopidy.backends.base import PlaybackController
from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd import dispatcher
from mopidy.mixers.dummy import DummyMixer
from mopidy.models import Track

from tests import SkipTest

PAUSED = PlaybackController.PAUSED
PLAYING = PlaybackController.PLAYING
STOPPED = PlaybackController.STOPPED

class PlaybackOptionsHandlerTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.h = dispatcher.MpdDispatcher()

    def tearDown(self):
        self.b.stop().get()
        self.mixer.stop().get()

    def test_consume_off(self):
        result = self.h.handle_request(u'consume "0"')
        self.assertFalse(self.b.playback.consume.get())
        self.assert_(u'OK' in result)

    def test_consume_off_without_quotes(self):
        result = self.h.handle_request(u'consume 0')
        self.assertFalse(self.b.playback.consume.get())
        self.assert_(u'OK' in result)

    def test_consume_on(self):
        result = self.h.handle_request(u'consume "1"')
        self.assertTrue(self.b.playback.consume.get())
        self.assert_(u'OK' in result)

    def test_consume_on_without_quotes(self):
        result = self.h.handle_request(u'consume 1')
        self.assertTrue(self.b.playback.consume.get())
        self.assert_(u'OK' in result)

    def test_crossfade(self):
        result = self.h.handle_request(u'crossfade "10"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_random_off(self):
        result = self.h.handle_request(u'random "0"')
        self.assertFalse(self.b.playback.random.get())
        self.assert_(u'OK' in result)

    def test_random_off_without_quotes(self):
        result = self.h.handle_request(u'random 0')
        self.assertFalse(self.b.playback.random.get())
        self.assert_(u'OK' in result)

    def test_random_on(self):
        result = self.h.handle_request(u'random "1"')
        self.assertTrue(self.b.playback.random.get())
        self.assert_(u'OK' in result)

    def test_random_on_without_quotes(self):
        result = self.h.handle_request(u'random 1')
        self.assertTrue(self.b.playback.random.get())
        self.assert_(u'OK' in result)

    def test_repeat_off(self):
        result = self.h.handle_request(u'repeat "0"')
        self.assertFalse(self.b.playback.repeat.get())
        self.assert_(u'OK' in result)

    def test_repeat_off_without_quotes(self):
        result = self.h.handle_request(u'repeat 0')
        self.assertFalse(self.b.playback.repeat.get())
        self.assert_(u'OK' in result)

    def test_repeat_on(self):
        result = self.h.handle_request(u'repeat "1"')
        self.assertTrue(self.b.playback.repeat.get())
        self.assert_(u'OK' in result)

    def test_repeat_on_without_quotes(self):
        result = self.h.handle_request(u'repeat 1')
        self.assertTrue(self.b.playback.repeat.get())
        self.assert_(u'OK' in result)

    def test_setvol_below_min(self):
        result = self.h.handle_request(u'setvol "-10"')
        self.assert_(u'OK' in result)
        self.assertEqual(0, self.mixer.volume.get())

    def test_setvol_min(self):
        result = self.h.handle_request(u'setvol "0"')
        self.assert_(u'OK' in result)
        self.assertEqual(0, self.mixer.volume.get())

    def test_setvol_middle(self):
        result = self.h.handle_request(u'setvol "50"')
        self.assert_(u'OK' in result)
        self.assertEqual(50, self.mixer.volume.get())

    def test_setvol_max(self):
        result = self.h.handle_request(u'setvol "100"')
        self.assert_(u'OK' in result)
        self.assertEqual(100, self.mixer.volume.get())

    def test_setvol_above_max(self):
        result = self.h.handle_request(u'setvol "110"')
        self.assert_(u'OK' in result)
        self.assertEqual(100, self.mixer.volume.get())

    def test_setvol_plus_is_ignored(self):
        result = self.h.handle_request(u'setvol "+10"')
        self.assert_(u'OK' in result)
        self.assertEqual(10, self.mixer.volume.get())

    def test_setvol_without_quotes(self):
        result = self.h.handle_request(u'setvol 50')
        self.assert_(u'OK' in result)
        self.assertEqual(50, self.mixer.volume.get())

    def test_single_off(self):
        result = self.h.handle_request(u'single "0"')
        self.assertFalse(self.b.playback.single.get())
        self.assert_(u'OK' in result)

    def test_single_off_without_quotes(self):
        result = self.h.handle_request(u'single 0')
        self.assertFalse(self.b.playback.single.get())
        self.assert_(u'OK' in result)

    def test_single_on(self):
        result = self.h.handle_request(u'single "1"')
        self.assertTrue(self.b.playback.single.get())
        self.assert_(u'OK' in result)

    def test_single_on_without_quotes(self):
        result = self.h.handle_request(u'single 1')
        self.assertTrue(self.b.playback.single.get())
        self.assert_(u'OK' in result)

    def test_replay_gain_mode_off(self):
        result = self.h.handle_request(u'replay_gain_mode "off"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_replay_gain_mode_track(self):
        result = self.h.handle_request(u'replay_gain_mode "track"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_replay_gain_mode_album(self):
        result = self.h.handle_request(u'replay_gain_mode "album"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_replay_gain_status_default(self):
        expected = u'off'
        result = self.h.handle_request(u'replay_gain_status')
        self.assert_(u'OK' in result)
        self.assert_(expected in result)

    def test_replay_gain_status_off(self):
        raise SkipTest
        expected = u'off'
        self.h._replay_gain_mode(expected)
        result = self.h.handle_request(u'replay_gain_status')
        self.assert_(u'OK' in result)
        self.assert_(expected in result)

    def test_replay_gain_status_track(self):
        raise SkipTest
        expected = u'track'
        self.h._replay_gain_mode(expected)
        result = self.h.handle_request(u'replay_gain_status')
        self.assert_(u'OK' in result)
        self.assert_(expected in result)

    def test_replay_gain_status_album(self):
        raise SkipTest
        expected = u'album'
        self.h._replay_gain_mode(expected)
        result = self.h.handle_request(u'replay_gain_status')
        self.assert_(u'OK' in result)
        self.assert_(expected in result)


class PlaybackControlHandlerTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.h = dispatcher.MpdDispatcher()

    def tearDown(self):
        self.b.stop().get()
        self.mixer.stop().get()

    def test_next(self):
        result = self.h.handle_request(u'next')
        self.assert_(u'OK' in result)

    def test_pause_off(self):
        self.b.current_playlist.append([Track()])
        self.h.handle_request(u'play "0"')
        self.h.handle_request(u'pause "1"')
        result = self.h.handle_request(u'pause "0"')
        self.assert_(u'OK' in result)
        self.assertEqual(PLAYING, self.b.playback.state.get())

    def test_pause_on(self):
        self.b.current_playlist.append([Track()])
        self.h.handle_request(u'play "0"')
        result = self.h.handle_request(u'pause "1"')
        self.assert_(u'OK' in result)
        self.assertEqual(PAUSED, self.b.playback.state.get())

    def test_pause_toggle(self):
        self.b.current_playlist.append([Track()])
        result = self.h.handle_request(u'play "0"')
        self.assert_(u'OK' in result)
        self.assertEqual(PLAYING, self.b.playback.state.get())
        result = self.h.handle_request(u'pause')
        self.assert_(u'OK' in result)
        self.assertEqual(PAUSED, self.b.playback.state.get())
        result = self.h.handle_request(u'pause')
        self.assert_(u'OK' in result)
        self.assertEqual(PLAYING, self.b.playback.state.get())

    def test_play_without_pos(self):
        self.b.current_playlist.append([Track()])
        self.b.playback.state = PAUSED
        result = self.h.handle_request(u'play')
        self.assert_(u'OK' in result)
        self.assertEqual(PLAYING, self.b.playback.state.get())

    def test_play_with_pos(self):
        self.b.current_playlist.append([Track()])
        result = self.h.handle_request(u'play "0"')
        self.assert_(u'OK' in result)
        self.assertEqual(PLAYING, self.b.playback.state.get())

    def test_play_with_pos_without_quotes(self):
        self.b.current_playlist.append([Track()])
        result = self.h.handle_request(u'play 0')
        self.assert_(u'OK' in result)
        self.assertEqual(PLAYING, self.b.playback.state.get())

    def test_play_with_pos_out_of_bounds(self):
        self.b.current_playlist.append([])
        result = self.h.handle_request(u'play "0"')
        self.assertEqual(result[0], u'ACK [2@0] {play} Bad song index')
        self.assertEqual(STOPPED, self.b.playback.state.get())

    def test_play_minus_one_plays_first_in_playlist_if_no_current_track(self):
        self.assertEqual(self.b.playback.current_track.get(), None)
        self.b.current_playlist.append([Track(uri='a'), Track(uri='b')])
        result = self.h.handle_request(u'play "-1"')
        self.assert_(u'OK' in result)
        self.assertEqual(PLAYING, self.b.playback.state.get())
        self.assertEqual(self.b.playback.current_track.get().uri, 'a')

    def test_play_minus_one_plays_current_track_if_current_track_is_set(self):
        self.b.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.assertEqual(self.b.playback.current_track.get(), None)
        self.b.playback.play()
        self.b.playback.next()
        self.b.playback.stop()
        self.assertNotEqual(self.b.playback.current_track.get(), None)
        result = self.h.handle_request(u'play "-1"')
        self.assert_(u'OK' in result)
        self.assertEqual(PLAYING, self.b.playback.state.get())
        self.assertEqual(self.b.playback.current_track.get().uri, 'b')

    def test_play_minus_one_on_empty_playlist_does_not_ack(self):
        self.b.current_playlist.clear()
        result = self.h.handle_request(u'play "-1"')
        self.assert_(u'OK' in result)
        self.assertEqual(STOPPED, self.b.playback.state.get())
        self.assertEqual(self.b.playback.current_track.get(), None)

    def test_play_minus_is_ignored_if_playing(self):
        self.b.current_playlist.append([Track(length=40000)])
        self.b.playback.seek(30000)
        self.assert_(self.b.playback.time_position.get() >= 30000)
        self.assertEquals(PLAYING, self.b.playback.state.get())
        result = self.h.handle_request(u'play "-1"')
        self.assert_(u'OK' in result)
        self.assertEqual(PLAYING, self.b.playback.state.get())
        self.assert_(self.b.playback.time_position.get() >= 30000)

    def test_play_minus_one_resumes_if_paused(self):
        self.b.current_playlist.append([Track(length=40000)])
        self.b.playback.seek(30000)
        self.assert_(self.b.playback.time_position.get() >= 30000)
        self.assertEquals(PLAYING, self.b.playback.state.get())
        self.b.playback.pause()
        self.assertEquals(PAUSED, self.b.playback.state.get())
        result = self.h.handle_request(u'play "-1"')
        self.assert_(u'OK' in result)
        self.assertEqual(PLAYING, self.b.playback.state.get())
        self.assert_(self.b.playback.time_position.get() >= 30000)

    def test_playid(self):
        self.b.current_playlist.append([Track()])
        result = self.h.handle_request(u'playid "0"')
        self.assert_(u'OK' in result)
        self.assertEqual(PLAYING, self.b.playback.state.get())

    def test_playid_minus_one_plays_first_in_playlist_if_no_current_track(self):
        self.assertEqual(self.b.playback.current_track.get(), None)
        self.b.current_playlist.append([Track(uri='a'), Track(uri='b')])
        result = self.h.handle_request(u'playid "-1"')
        self.assert_(u'OK' in result)
        self.assertEqual(PLAYING, self.b.playback.state.get())
        self.assertEqual(self.b.playback.current_track.get().uri, 'a')

    def test_playid_minus_one_plays_current_track_if_current_track_is_set(self):
        self.b.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.assertEqual(self.b.playback.current_track.get(), None)
        self.b.playback.play()
        self.b.playback.next()
        self.b.playback.stop()
        self.assertNotEqual(self.b.playback.current_track.get(), None)
        result = self.h.handle_request(u'playid "-1"')
        self.assert_(u'OK' in result)
        self.assertEqual(PLAYING, self.b.playback.state.get())
        self.assertEqual(self.b.playback.current_track.get().uri, 'b')

    def test_playid_minus_one_on_empty_playlist_does_not_ack(self):
        self.b.current_playlist.clear()
        result = self.h.handle_request(u'playid "-1"')
        self.assert_(u'OK' in result)
        self.assertEqual(STOPPED, self.b.playback.state.get())
        self.assertEqual(self.b.playback.current_track.get(), None)

    def test_playid_minus_is_ignored_if_playing(self):
        self.b.current_playlist.append([Track(length=40000)])
        self.b.playback.seek(30000)
        self.assert_(self.b.playback.time_position.get() >= 30000)
        self.assertEquals(PLAYING, self.b.playback.state.get())
        result = self.h.handle_request(u'playid "-1"')
        self.assert_(u'OK' in result)
        self.assertEqual(PLAYING, self.b.playback.state.get())
        self.assert_(self.b.playback.time_position.get() >= 30000)

    def test_playid_minus_one_resumes_if_paused(self):
        self.b.current_playlist.append([Track(length=40000)])
        self.b.playback.seek(30000)
        self.assert_(self.b.playback.time_position.get() >= 30000)
        self.assertEquals(PLAYING, self.b.playback.state.get())
        self.b.playback.pause()
        self.assertEquals(PAUSED, self.b.playback.state.get())
        result = self.h.handle_request(u'playid "-1"')
        self.assert_(u'OK' in result)
        self.assertEqual(PLAYING, self.b.playback.state.get())
        self.assert_(self.b.playback.time_position.get() >= 30000)

    def test_playid_which_does_not_exist(self):
        self.b.current_playlist.append([Track()])
        result = self.h.handle_request(u'playid "12345"')
        self.assertEqual(result[0], u'ACK [50@0] {playid} No such song')

    def test_previous(self):
        result = self.h.handle_request(u'previous')
        self.assert_(u'OK' in result)

    def test_seek(self):
        self.b.current_playlist.append([Track(length=40000)])
        self.h.handle_request(u'seek "0"')
        result = self.h.handle_request(u'seek "0" "30"')
        self.assert_(u'OK' in result)
        self.assert_(self.b.playback.time_position >= 30000)

    def test_seek_with_songpos(self):
        seek_track = Track(uri='2', length=40000)
        self.b.current_playlist.append(
            [Track(uri='1', length=40000), seek_track])
        result = self.h.handle_request(u'seek "1" "30"')
        self.assert_(u'OK' in result)
        self.assertEqual(self.b.playback.current_track.get(), seek_track)

    def test_seek_without_quotes(self):
        self.b.current_playlist.append([Track(length=40000)])
        self.h.handle_request(u'seek 0')
        result = self.h.handle_request(u'seek 0 30')
        self.assert_(u'OK' in result)
        self.assert_(self.b.playback.time_position.get() >= 30000)

    def test_seekid(self):
        self.b.current_playlist.append([Track(length=40000)])
        result = self.h.handle_request(u'seekid "0" "30"')
        self.assert_(u'OK' in result)
        self.assert_(self.b.playback.time_position.get() >= 30000)

    def test_seekid_with_cpid(self):
        seek_track = Track(uri='2', length=40000)
        self.b.current_playlist.append(
            [Track(length=40000), seek_track])
        result = self.h.handle_request(u'seekid "1" "30"')
        self.assert_(u'OK' in result)
        self.assertEqual(self.b.playback.current_cpid.get(), 1)
        self.assertEqual(self.b.playback.current_track.get(), seek_track)

    def test_stop(self):
        result = self.h.handle_request(u'stop')
        self.assert_(u'OK' in result)
        self.assertEqual(STOPPED, self.b.playback.state.get())
