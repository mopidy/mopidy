from mopidy.backends import dummy
from mopidy.core import PlaybackState
from mopidy.frontends.mpd import dispatcher
from mopidy.frontends.mpd.protocol import status
from mopidy.models import Track

from tests import unittest


PAUSED = PlaybackState.PAUSED
PLAYING = PlaybackState.PLAYING
STOPPED = PlaybackState.STOPPED

# FIXME migrate to using protocol.BaseTestCase instead of status.stats
# directly?


class StatusHandlerTest(unittest.TestCase):
    def setUp(self):
        self.backend = dummy.DummyBackend.start().proxy()
        self.dispatcher = dispatcher.MpdDispatcher()
        self.context = self.dispatcher.context

    def tearDown(self):
        self.backend.stop().get()

    def test_stats_method(self):
        result = status.stats(self.context)
        self.assertIn('artists', result)
        self.assert_(int(result['artists']) >= 0)
        self.assertIn('albums', result)
        self.assert_(int(result['albums']) >= 0)
        self.assertIn('songs', result)
        self.assert_(int(result['songs']) >= 0)
        self.assertIn('uptime', result)
        self.assert_(int(result['uptime']) >= 0)
        self.assertIn('db_playtime', result)
        self.assert_(int(result['db_playtime']) >= 0)
        self.assertIn('db_update', result)
        self.assert_(int(result['db_update']) >= 0)
        self.assertIn('playtime', result)
        self.assert_(int(result['playtime']) >= 0)

    def test_status_method_contains_volume_with_na_value(self):
        result = dict(status.status(self.context))
        self.assertIn('volume', result)
        self.assertEqual(int(result['volume']), -1)

    def test_status_method_contains_volume(self):
        self.backend.playback.volume = 17
        result = dict(status.status(self.context))
        self.assertIn('volume', result)
        self.assertEqual(int(result['volume']), 17)

    def test_status_method_contains_repeat_is_0(self):
        result = dict(status.status(self.context))
        self.assertIn('repeat', result)
        self.assertEqual(int(result['repeat']), 0)

    def test_status_method_contains_repeat_is_1(self):
        self.backend.playback.repeat = 1
        result = dict(status.status(self.context))
        self.assertIn('repeat', result)
        self.assertEqual(int(result['repeat']), 1)

    def test_status_method_contains_random_is_0(self):
        result = dict(status.status(self.context))
        self.assertIn('random', result)
        self.assertEqual(int(result['random']), 0)

    def test_status_method_contains_random_is_1(self):
        self.backend.playback.random = 1
        result = dict(status.status(self.context))
        self.assertIn('random', result)
        self.assertEqual(int(result['random']), 1)

    def test_status_method_contains_single(self):
        result = dict(status.status(self.context))
        self.assertIn('single', result)
        self.assertIn(int(result['single']), (0, 1))

    def test_status_method_contains_consume_is_0(self):
        result = dict(status.status(self.context))
        self.assertIn('consume', result)
        self.assertEqual(int(result['consume']), 0)

    def test_status_method_contains_consume_is_1(self):
        self.backend.playback.consume = 1
        result = dict(status.status(self.context))
        self.assertIn('consume', result)
        self.assertEqual(int(result['consume']), 1)

    def test_status_method_contains_playlist(self):
        result = dict(status.status(self.context))
        self.assertIn('playlist', result)
        self.assertIn(int(result['playlist']), xrange(0, 2**31 - 1))

    def test_status_method_contains_playlistlength(self):
        result = dict(status.status(self.context))
        self.assertIn('playlistlength', result)
        self.assert_(int(result['playlistlength']) >= 0)

    def test_status_method_contains_xfade(self):
        result = dict(status.status(self.context))
        self.assertIn('xfade', result)
        self.assert_(int(result['xfade']) >= 0)

    def test_status_method_contains_state_is_play(self):
        self.backend.playback.state = PLAYING
        result = dict(status.status(self.context))
        self.assertIn('state', result)
        self.assertEqual(result['state'], 'play')

    def test_status_method_contains_state_is_stop(self):
        self.backend.playback.state = STOPPED
        result = dict(status.status(self.context))
        self.assertIn('state', result)
        self.assertEqual(result['state'], 'stop')

    def test_status_method_contains_state_is_pause(self):
        self.backend.playback.state = PLAYING
        self.backend.playback.state = PAUSED
        result = dict(status.status(self.context))
        self.assertIn('state', result)
        self.assertEqual(result['state'], 'pause')

    def test_status_method_when_playlist_loaded_contains_song(self):
        self.backend.current_playlist.append([Track()])
        self.backend.playback.play()
        result = dict(status.status(self.context))
        self.assertIn('song', result)
        self.assert_(int(result['song']) >= 0)

    def test_status_method_when_playlist_loaded_contains_cpid_as_songid(self):
        self.backend.current_playlist.append([Track()])
        self.backend.playback.play()
        result = dict(status.status(self.context))
        self.assertIn('songid', result)
        self.assertEqual(int(result['songid']), 0)

    def test_status_method_when_playing_contains_time_with_no_length(self):
        self.backend.current_playlist.append([Track(length=None)])
        self.backend.playback.play()
        result = dict(status.status(self.context))
        self.assertIn('time', result)
        (position, total) = result['time'].split(':')
        position = int(position)
        total = int(total)
        self.assert_(position <= total)

    def test_status_method_when_playing_contains_time_with_length(self):
        self.backend.current_playlist.append([Track(length=10000)])
        self.backend.playback.play()
        result = dict(status.status(self.context))
        self.assertIn('time', result)
        (position, total) = result['time'].split(':')
        position = int(position)
        total = int(total)
        self.assert_(position <= total)

    def test_status_method_when_playing_contains_elapsed(self):
        self.backend.playback.state = PAUSED
        self.backend.playback.play_time_accumulated = 59123
        result = dict(status.status(self.context))
        self.assertIn('elapsed', result)
        self.assertEqual(result['elapsed'], '59.123')

    def test_status_method_when_starting_playing_contains_elapsed_zero(self):
        self.backend.playback.state = PAUSED
        self.backend.playback.play_time_accumulated = 123 # Less than 1000ms
        result = dict(status.status(self.context))
        self.assertIn('elapsed', result)
        self.assertEqual(result['elapsed'], '0.123')

    def test_status_method_when_playing_contains_bitrate(self):
        self.backend.current_playlist.append([Track(bitrate=320)])
        self.backend.playback.play()
        result = dict(status.status(self.context))
        self.assertIn('bitrate', result)
        self.assertEqual(int(result['bitrate']), 320)
