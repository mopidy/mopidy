from mopidy.backends import dummy as backend
from mopidy.frontends.mpd import dispatcher
from mopidy.frontends.mpd.protocol import status
from mopidy.mixers import dummy as mixer
from mopidy.models import Track

from tests import unittest

PAUSED = backend.PlaybackController.PAUSED
PLAYING = backend.PlaybackController.PLAYING
STOPPED = backend.PlaybackController.STOPPED

# FIXME migrate to using protocol.BaseTestCase instead of status.stats
# directly?


class StatusHandlerTest(unittest.TestCase):
    def setUp(self):
        self.backend = backend.DummyBackend.start().proxy()
        self.mixer = mixer.DummyMixer.start().proxy()
        self.dispatcher = dispatcher.MpdDispatcher()
        self.context = self.dispatcher.context

    def tearDown(self):
        self.backend.stop().get()
        self.mixer.stop().get()

    def test_stats_method(self):
        result = status.stats(self.context)
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

    def test_status_method_contains_volume_which_defaults_to_0(self):
        result = dict(status.status(self.context))
        self.assert_('volume' in result)
        self.assertEqual(int(result['volume']), 0)

    def test_status_method_contains_volume(self):
        self.mixer.volume = 17
        result = dict(status.status(self.context))
        self.assert_('volume' in result)
        self.assertEqual(int(result['volume']), 17)

    def test_status_method_contains_repeat_is_0(self):
        result = dict(status.status(self.context))
        self.assert_('repeat' in result)
        self.assertEqual(int(result['repeat']), 0)

    def test_status_method_contains_repeat_is_1(self):
        self.backend.playback.repeat = 1
        result = dict(status.status(self.context))
        self.assert_('repeat' in result)
        self.assertEqual(int(result['repeat']), 1)

    def test_status_method_contains_random_is_0(self):
        result = dict(status.status(self.context))
        self.assert_('random' in result)
        self.assertEqual(int(result['random']), 0)

    def test_status_method_contains_random_is_1(self):
        self.backend.playback.random = 1
        result = dict(status.status(self.context))
        self.assert_('random' in result)
        self.assertEqual(int(result['random']), 1)

    def test_status_method_contains_single(self):
        result = dict(status.status(self.context))
        self.assert_('single' in result)
        self.assert_(int(result['single']) in (0, 1))

    def test_status_method_contains_consume_is_0(self):
        result = dict(status.status(self.context))
        self.assert_('consume' in result)
        self.assertEqual(int(result['consume']), 0)

    def test_status_method_contains_consume_is_1(self):
        self.backend.playback.consume = 1
        result = dict(status.status(self.context))
        self.assert_('consume' in result)
        self.assertEqual(int(result['consume']), 1)

    def test_status_method_contains_playlist(self):
        result = dict(status.status(self.context))
        self.assert_('playlist' in result)
        self.assert_(int(result['playlist']) in xrange(0, 2**31 - 1))

    def test_status_method_contains_playlistlength(self):
        result = dict(status.status(self.context))
        self.assert_('playlistlength' in result)
        self.assert_(int(result['playlistlength']) >= 0)

    def test_status_method_contains_xfade(self):
        result = dict(status.status(self.context))
        self.assert_('xfade' in result)
        self.assert_(int(result['xfade']) >= 0)

    def test_status_method_contains_state_is_play(self):
        self.backend.playback.state = PLAYING
        result = dict(status.status(self.context))
        self.assert_('state' in result)
        self.assertEqual(result['state'], 'play')

    def test_status_method_contains_state_is_stop(self):
        self.backend.playback.state = STOPPED
        result = dict(status.status(self.context))
        self.assert_('state' in result)
        self.assertEqual(result['state'], 'stop')

    def test_status_method_contains_state_is_pause(self):
        self.backend.playback.state = PLAYING
        self.backend.playback.state = PAUSED
        result = dict(status.status(self.context))
        self.assert_('state' in result)
        self.assertEqual(result['state'], 'pause')

    def test_status_method_when_playlist_loaded_contains_song(self):
        self.backend.current_playlist.append([Track()])
        self.backend.playback.play()
        result = dict(status.status(self.context))
        self.assert_('song' in result)
        self.assert_(int(result['song']) >= 0)

    def test_status_method_when_playlist_loaded_contains_cpid_as_songid(self):
        self.backend.current_playlist.append([Track()])
        self.backend.playback.play()
        result = dict(status.status(self.context))
        self.assert_('songid' in result)
        self.assertEqual(int(result['songid']), 0)

    def test_status_method_when_playing_contains_time_with_no_length(self):
        self.backend.current_playlist.append([Track(length=None)])
        self.backend.playback.play()
        result = dict(status.status(self.context))
        self.assert_('time' in result)
        (position, total) = result['time'].split(':')
        position = int(position)
        total = int(total)
        self.assert_(position <= total)

    def test_status_method_when_playing_contains_time_with_length(self):
        self.backend.current_playlist.append([Track(length=10000)])
        self.backend.playback.play()
        result = dict(status.status(self.context))
        self.assert_('time' in result)
        (position, total) = result['time'].split(':')
        position = int(position)
        total = int(total)
        self.assert_(position <= total)

    def test_status_method_when_playing_contains_elapsed(self):
        self.backend.playback.state = PAUSED
        self.backend.playback.play_time_accumulated = 59123
        result = dict(status.status(self.context))
        self.assert_('elapsed' in result)
        self.assertEqual(result['elapsed'], '59.123')

    def test_status_method_when_starting_playing_contains_elapsed_zero(self):
        self.backend.playback.state = PAUSED
        self.backend.playback.play_time_accumulated = 123 # Less than 1000ms
        result = dict(status.status(self.context))
        self.assert_('elapsed' in result)
        self.assertEqual(result['elapsed'], '0.123')

    def test_status_method_when_playing_contains_bitrate(self):
        self.backend.current_playlist.append([Track(bitrate=320)])
        self.backend.playback.play()
        result = dict(status.status(self.context))
        self.assert_('bitrate' in result)
        self.assertEqual(int(result['bitrate']), 320)
