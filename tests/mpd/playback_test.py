import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.mixers.dummy import DummyMixer
from mopidy.models import Track
from mopidy.mpd import frontend

class PlaybackOptionsHandlerTest(unittest.TestCase):
    def setUp(self):
        self.m = DummyMixer()
        self.b = DummyBackend(mixer=self.m)
        self.h = frontend.MpdFrontend(backend=self.b)

    def test_consume_off(self):
        result = self.h.handle_request(u'consume "0"')
        self.assertFalse(self.b.playback.consume)
        self.assert_(u'OK' in result)

    def test_consume_on(self):
        result = self.h.handle_request(u'consume "1"')
        self.assertTrue(self.b.playback.consume)
        self.assert_(u'OK' in result)

    def test_crossfade(self):
        result = self.h.handle_request(u'crossfade "10"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_random_off(self):
        result = self.h.handle_request(u'random "0"')
        self.assertFalse(self.b.playback.random)
        self.assert_(u'OK' in result)

    def test_random_on(self):
        result = self.h.handle_request(u'random "1"')
        self.assertTrue(self.b.playback.random)
        self.assert_(u'OK' in result)

    def test_repeat_off(self):
        result = self.h.handle_request(u'repeat "0"')
        self.assertFalse(self.b.playback.repeat)
        self.assert_(u'OK' in result)

    def test_repeat_on(self):
        result = self.h.handle_request(u'repeat "1"')
        self.assertTrue(self.b.playback.repeat)
        self.assert_(u'OK' in result)

    def test_setvol_below_min(self):
        result = self.h.handle_request(u'setvol "-10"')
        self.assert_(u'OK' in result)
        self.assertEqual(0, self.b.mixer.volume)

    def test_setvol_min(self):
        result = self.h.handle_request(u'setvol "0"')
        self.assert_(u'OK' in result)
        self.assertEqual(0, self.b.mixer.volume)

    def test_setvol_middle(self):
        result = self.h.handle_request(u'setvol "50"')
        self.assert_(u'OK' in result)
        self.assertEqual(50, self.b.mixer.volume)

    def test_setvol_max(self):
        result = self.h.handle_request(u'setvol "100"')
        self.assert_(u'OK' in result)
        self.assertEqual(100, self.b.mixer.volume)

    def test_setvol_above_max(self):
        result = self.h.handle_request(u'setvol "110"')
        self.assert_(u'OK' in result)
        self.assertEqual(100, self.b.mixer.volume)

    def test_setvol_plus_is_ignored(self):
        result = self.h.handle_request(u'setvol "+10"')
        self.assert_(u'OK' in result)
        self.assertEqual(10, self.b.mixer.volume)

    def test_single_off(self):
        result = self.h.handle_request(u'single "0"')
        self.assertFalse(self.b.playback.single)
        self.assert_(u'OK' in result)

    def test_single_on(self):
        result = self.h.handle_request(u'single "1"')
        self.assertTrue(self.b.playback.single)
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

    #def test_replay_gain_status_off(self):
    #    expected = u'off'
    #    self.h._replay_gain_mode(expected)
    #    result = self.h.handle_request(u'replay_gain_status')
    #    self.assert_(u'OK' in result)
    #    self.assert_(expected in result)

    #def test_replay_gain_status_track(self):
    #    expected = u'track'
    #    self.h._replay_gain_mode(expected)
    #    result = self.h.handle_request(u'replay_gain_status')
    #    self.assert_(u'OK' in result)
    #    self.assert_(expected in result)

    #def test_replay_gain_status_album(self):
    #    expected = u'album'
    #    self.h._replay_gain_mode(expected)
    #    result = self.h.handle_request(u'replay_gain_status')
    #    self.assert_(u'OK' in result)
    #    self.assert_(expected in result)


class PlaybackControlHandlerTest(unittest.TestCase):
    def setUp(self):
        self.m = DummyMixer()
        self.b = DummyBackend(mixer=self.m)
        self.h = frontend.MpdFrontend(backend=self.b)

    def test_next(self):
        result = self.h.handle_request(u'next')
        self.assert_(u'OK' in result)

    def test_pause_off(self):
        track = Track()
        self.b.current_playlist.load([track])
        self.h.handle_request(u'play "0"')
        self.h.handle_request(u'pause "1"')
        result = self.h.handle_request(u'pause "0"')
        self.assert_(u'OK' in result)
        self.assertEqual(self.b.playback.PLAYING, self.b.playback.state)

    def test_pause_on(self):
        track = Track()
        self.b.current_playlist.load([track])
        self.h.handle_request(u'play "0"')
        result = self.h.handle_request(u'pause "1"')
        self.assert_(u'OK' in result)
        self.assertEqual(self.b.playback.PAUSED, self.b.playback.state)

    def test_play_without_pos(self):
        track = Track()
        self.b.current_playlist.load([track])
        self.b.playback.state = self.b.playback.PAUSED
        result = self.h.handle_request(u'play')
        self.assert_(u'OK' in result)
        self.assertEqual(self.b.playback.PLAYING, self.b.playback.state)

    def test_play_with_pos(self):
        self.b.current_playlist.load([Track()])
        result = self.h.handle_request(u'play "0"')
        self.assert_(u'OK' in result)
        self.assertEqual(self.b.playback.PLAYING, self.b.playback.state)

    def test_play_with_pos_out_of_bounds(self):
        self.b.current_playlist.load([])
        result = self.h.handle_request(u'play "0"')
        self.assertEqual(result[0], u'ACK [2@0] {play} Bad song index')
        self.assertEqual(self.b.playback.STOPPED, self.b.playback.state)

    def test_play_minus_one_plays_first_in_playlist(self):
        track = Track()
        self.b.current_playlist.load([track])
        result = self.h.handle_request(u'play "-1"')
        self.assert_(u'OK' in result)
        self.assertEqual(self.b.playback.PLAYING, self.b.playback.state)
        self.assertEqual(self.b.playback.current_track, track)

    def test_play_minus_one_on_empty_playlist_does_not_ack(self):
        self.b.current_playlist.clear()
        result = self.h.handle_request(u'play "-1"')
        self.assert_(u'OK' in result)
        self.assertEqual(self.b.playback.STOPPED, self.b.playback.state)
        self.assertEqual(self.b.playback.current_track, None)

    def test_playid(self):
        self.b.current_playlist.load([Track()])
        result = self.h.handle_request(u'playid "1"')
        self.assert_(u'OK' in result)
        self.assertEqual(self.b.playback.PLAYING, self.b.playback.state)

    def test_playid_minus_one_plays_first_in_playlist(self):
        track = Track()
        self.b.current_playlist.load([track])
        result = self.h.handle_request(u'playid "-1"')
        self.assert_(u'OK' in result)
        self.assertEqual(self.b.playback.PLAYING, self.b.playback.state)
        self.assertEqual(self.b.playback.current_track, track)

    def test_playid_minus_one_on_empty_playlist_does_not_ack(self):
        self.b.current_playlist.clear()
        result = self.h.handle_request(u'playid "-1"')
        self.assert_(u'OK' in result)
        self.assertEqual(self.b.playback.STOPPED, self.b.playback.state)
        self.assertEqual(self.b.playback.current_track, None)

    def test_playid_which_does_not_exist(self):
        self.b.current_playlist.load([Track()])
        result = self.h.handle_request(u'playid "12345"')
        self.assertEqual(result[0], u'ACK [50@0] {playid} No such song')

    def test_previous(self):
        result = self.h.handle_request(u'previous')
        self.assert_(u'OK' in result)

    def test_seek(self):
        result = self.h.handle_request(u'seek "0" "30"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_seekid(self):
        result = self.h.handle_request(u'seekid "0" "30"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_stop(self):
        result = self.h.handle_request(u'stop')
        self.assert_(u'OK' in result)
        self.assertEqual(self.b.playback.STOPPED, self.b.playback.state)
