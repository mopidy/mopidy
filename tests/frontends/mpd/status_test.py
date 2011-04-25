import unittest

from mopidy.backends.base import PlaybackController
from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd import dispatcher
from mopidy.mixers.dummy import DummyMixer
from mopidy.models import Track

PAUSED = PlaybackController.PAUSED
PLAYING = PlaybackController.PLAYING
STOPPED = PlaybackController.STOPPED

class StatusHandlerTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.h = dispatcher.MpdDispatcher()

    def tearDown(self):
        self.b.stop().get()
        self.mixer.stop().get()

    def test_clearerror(self):
        result = self.h.handle_request(u'clearerror')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_currentsong(self):
        track = Track()
        self.b.current_playlist.append([track])
        self.b.playback.play()
        result = self.h.handle_request(u'currentsong')
        self.assert_(u'file: ' in result)
        self.assert_(u'Time: 0' in result)
        self.assert_(u'Artist: ' in result)
        self.assert_(u'Title: ' in result)
        self.assert_(u'Album: ' in result)
        self.assert_(u'Track: 0' in result)
        self.assert_(u'Date: ' in result)
        self.assert_(u'Pos: 0' in result)
        self.assert_(u'Id: 0' in result)
        self.assert_(u'OK' in result)

    def test_currentsong_without_song(self):
        result = self.h.handle_request(u'currentsong')
        self.assert_(u'OK' in result)

    def test_idle_without_subsystems(self):
        result = self.h.handle_request(u'idle')
        self.assert_(u'OK' in result)

    def test_idle_with_subsystems(self):
        result = self.h.handle_request(u'idle database playlist')
        self.assert_(u'OK' in result)

    def test_noidle(self):
        result = self.h.handle_request(u'noidle')
        self.assert_(u'OK' in result)

    def test_stats_command(self):
        result = self.h.handle_request(u'stats')
        self.assert_(u'OK' in result)

    def test_stats_method(self):
        result = dispatcher.status.stats(self.h)
        self.assert_('artists' in result)
        self.assert_(int(result['artists']) >= 0)
        self.assert_('albums' in result)
        self.assert_(int(result['albums']) >= 0)
        self.assert_('songs' in result)
        self.assert_(int(result['songs']) >= 0)
        self.assert_('uptime' in result)
        self.assert_(int(result['uptime']) >= 0)
        self.assert_('db_playtime' in result)
        self.assert_(int(result['db_playtime']) >= 0)
        self.assert_('db_update' in result)
        self.assert_(int(result['db_update']) >= 0)
        self.assert_('playtime' in result)
        self.assert_(int(result['playtime']) >= 0)

    def test_status_command(self):
        result = self.h.handle_request(u'status')
        self.assert_(u'OK' in result)

    def test_status_method_contains_volume_which_defaults_to_0(self):
        result = dict(dispatcher.status.status(self.h))
        self.assert_('volume' in result)
        self.assertEqual(int(result['volume']), 0)

    def test_status_method_contains_volume(self):
        self.mixer.volume = 17
        result = dict(dispatcher.status.status(self.h))
        self.assert_('volume' in result)
        self.assertEqual(int(result['volume']), 17)

    def test_status_method_contains_repeat_is_0(self):
        result = dict(dispatcher.status.status(self.h))
        self.assert_('repeat' in result)
        self.assertEqual(int(result['repeat']), 0)

    def test_status_method_contains_repeat_is_1(self):
        self.b.playback.repeat = 1
        result = dict(dispatcher.status.status(self.h))
        self.assert_('repeat' in result)
        self.assertEqual(int(result['repeat']), 1)

    def test_status_method_contains_random_is_0(self):
        result = dict(dispatcher.status.status(self.h))
        self.assert_('random' in result)
        self.assertEqual(int(result['random']), 0)

    def test_status_method_contains_random_is_1(self):
        self.b.playback.random = 1
        result = dict(dispatcher.status.status(self.h))
        self.assert_('random' in result)
        self.assertEqual(int(result['random']), 1)

    def test_status_method_contains_single(self):
        result = dict(dispatcher.status.status(self.h))
        self.assert_('single' in result)
        self.assert_(int(result['single']) in (0, 1))

    def test_status_method_contains_consume_is_0(self):
        result = dict(dispatcher.status.status(self.h))
        self.assert_('consume' in result)
        self.assertEqual(int(result['consume']), 0)

    def test_status_method_contains_consume_is_1(self):
        self.b.playback.consume = 1
        result = dict(dispatcher.status.status(self.h))
        self.assert_('consume' in result)
        self.assertEqual(int(result['consume']), 1)

    def test_status_method_contains_playlist(self):
        result = dict(dispatcher.status.status(self.h))
        self.assert_('playlist' in result)
        self.assert_(int(result['playlist']) in xrange(0, 2**31 - 1))

    def test_status_method_contains_playlistlength(self):
        result = dict(dispatcher.status.status(self.h))
        self.assert_('playlistlength' in result)
        self.assert_(int(result['playlistlength']) >= 0)

    def test_status_method_contains_xfade(self):
        result = dict(dispatcher.status.status(self.h))
        self.assert_('xfade' in result)
        self.assert_(int(result['xfade']) >= 0)

    def test_status_method_contains_state_is_play(self):
        self.b.playback.state = PLAYING
        result = dict(dispatcher.status.status(self.h))
        self.assert_('state' in result)
        self.assertEqual(result['state'], 'play')

    def test_status_method_contains_state_is_stop(self):
        self.b.playback.state = STOPPED
        result = dict(dispatcher.status.status(self.h))
        self.assert_('state' in result)
        self.assertEqual(result['state'], 'stop')

    def test_status_method_contains_state_is_pause(self):
        self.b.playback.state = PLAYING
        self.b.playback.state = PAUSED
        result = dict(dispatcher.status.status(self.h))
        self.assert_('state' in result)
        self.assertEqual(result['state'], 'pause')

    def test_status_method_when_playlist_loaded_contains_song(self):
        self.b.current_playlist.append([Track()])
        self.b.playback.play()
        result = dict(dispatcher.status.status(self.h))
        self.assert_('song' in result)
        self.assert_(int(result['song']) >= 0)

    def test_status_method_when_playlist_loaded_contains_cpid_as_songid(self):
        self.b.current_playlist.append([Track()])
        self.b.playback.play()
        result = dict(dispatcher.status.status(self.h))
        self.assert_('songid' in result)
        self.assertEqual(int(result['songid']), 0)

    def test_status_method_when_playing_contains_time_with_no_length(self):
        self.b.current_playlist.append([Track(length=None)])
        self.b.playback.play()
        result = dict(dispatcher.status.status(self.h))
        self.assert_('time' in result)
        (position, total) = result['time'].split(':')
        position = int(position)
        total = int(total)
        self.assert_(position <= total)

    def test_status_method_when_playing_contains_time_with_length(self):
        self.b.current_playlist.append([Track(length=10000)])
        self.b.playback.play()
        result = dict(dispatcher.status.status(self.h))
        self.assert_('time' in result)
        (position, total) = result['time'].split(':')
        position = int(position)
        total = int(total)
        self.assert_(position <= total)

    def test_status_method_when_playing_contains_elapsed(self):
        self.b.playback.state = PAUSED
        self.b.playback.play_time_accumulated = 59123
        result = dict(dispatcher.status.status(self.h))
        self.assert_('elapsed' in result)
        self.assertEqual(int(result['elapsed']), 59123)

    def test_status_method_when_playing_contains_bitrate(self):
        self.b.current_playlist.append([Track(bitrate=320)])
        self.b.playback.play()
        result = dict(dispatcher.status.status(self.h))
        self.assert_('bitrate' in result)
        self.assertEqual(int(result['bitrate']), 320)
