from __future__ import unicode_literals

import unittest

import pykka

from mopidy import core
from mopidy.backends import dummy
from mopidy.core import PlaybackState
from mopidy.frontends.mpd import dispatcher
from mopidy.frontends.mpd.protocol import status
from mopidy.models import Track


PAUSED = PlaybackState.PAUSED
PLAYING = PlaybackState.PLAYING
STOPPED = PlaybackState.STOPPED

# FIXME migrate to using protocol.BaseTestCase instead of status.stats
# directly?


class StatusHandlerTest(unittest.TestCase):
    def setUp(self):
        self.backend = dummy.create_dummy_backend_proxy()
        self.core = core.Core.start(backends=[self.backend]).proxy()
        self.dispatcher = dispatcher.MpdDispatcher(core=self.core)
        self.context = self.dispatcher.context

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_stats_method(self):
        result = status.stats(self.context)
        self.assertIn('artists', result)
        self.assertGreaterEqual(int(result['artists']), 0)
        self.assertIn('albums', result)
        self.assertGreaterEqual(int(result['albums']), 0)
        self.assertIn('songs', result)
        self.assertGreaterEqual(int(result['songs']), 0)
        self.assertIn('uptime', result)
        self.assertGreaterEqual(int(result['uptime']), 0)
        self.assertIn('db_playtime', result)
        self.assertGreaterEqual(int(result['db_playtime']), 0)
        self.assertIn('db_update', result)
        self.assertGreaterEqual(int(result['db_update']), 0)
        self.assertIn('playtime', result)
        self.assertGreaterEqual(int(result['playtime']), 0)

    def test_status_method_contains_volume_with_na_value(self):
        result = dict(status.status(self.context))
        self.assertIn('volume', result)
        self.assertEqual(int(result['volume']), -1)

    def test_status_method_contains_volume(self):
        self.core.playback.volume = 17
        result = dict(status.status(self.context))
        self.assertIn('volume', result)
        self.assertEqual(int(result['volume']), 17)

    def test_status_method_contains_repeat_is_0(self):
        result = dict(status.status(self.context))
        self.assertIn('repeat', result)
        self.assertEqual(int(result['repeat']), 0)

    def test_status_method_contains_repeat_is_1(self):
        self.core.tracklist.repeat = 1
        result = dict(status.status(self.context))
        self.assertIn('repeat', result)
        self.assertEqual(int(result['repeat']), 1)

    def test_status_method_contains_random_is_0(self):
        result = dict(status.status(self.context))
        self.assertIn('random', result)
        self.assertEqual(int(result['random']), 0)

    def test_status_method_contains_random_is_1(self):
        self.core.tracklist.random = 1
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
        self.core.tracklist.consume = 1
        result = dict(status.status(self.context))
        self.assertIn('consume', result)
        self.assertEqual(int(result['consume']), 1)

    def test_status_method_contains_playlist(self):
        result = dict(status.status(self.context))
        self.assertIn('playlist', result)
        self.assertIn(int(result['playlist']), xrange(0, 2 ** 31 - 1))

    def test_status_method_contains_playlistlength(self):
        result = dict(status.status(self.context))
        self.assertIn('playlistlength', result)
        self.assertGreaterEqual(int(result['playlistlength']), 0)

    def test_status_method_contains_xfade(self):
        result = dict(status.status(self.context))
        self.assertIn('xfade', result)
        self.assertGreaterEqual(int(result['xfade']), 0)

    def test_status_method_contains_state_is_play(self):
        self.core.playback.state = PLAYING
        result = dict(status.status(self.context))
        self.assertIn('state', result)
        self.assertEqual(result['state'], 'play')

    def test_status_method_contains_state_is_stop(self):
        self.core.playback.state = STOPPED
        result = dict(status.status(self.context))
        self.assertIn('state', result)
        self.assertEqual(result['state'], 'stop')

    def test_status_method_contains_state_is_pause(self):
        self.core.playback.state = PLAYING
        self.core.playback.state = PAUSED
        result = dict(status.status(self.context))
        self.assertIn('state', result)
        self.assertEqual(result['state'], 'pause')

    def test_status_method_when_playlist_loaded_contains_song(self):
        self.core.tracklist.add([Track(uri='dummy:a')])
        self.core.playback.play()
        result = dict(status.status(self.context))
        self.assertIn('song', result)
        self.assertGreaterEqual(int(result['song']), 0)

    def test_status_method_when_playlist_loaded_contains_tlid_as_songid(self):
        self.core.tracklist.add([Track(uri='dummy:a')])
        self.core.playback.play()
        result = dict(status.status(self.context))
        self.assertIn('songid', result)
        self.assertEqual(int(result['songid']), 0)

    def test_status_method_when_playing_contains_time_with_no_length(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=None)])
        self.core.playback.play()
        result = dict(status.status(self.context))
        self.assertIn('time', result)
        (position, total) = result['time'].split(':')
        position = int(position)
        total = int(total)
        self.assertLessEqual(position, total)

    def test_status_method_when_playing_contains_time_with_length(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=10000)])
        self.core.playback.play()
        result = dict(status.status(self.context))
        self.assertIn('time', result)
        (position, total) = result['time'].split(':')
        position = int(position)
        total = int(total)
        self.assertLessEqual(position, total)

    def test_status_method_when_playing_contains_elapsed(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=60000)])
        self.core.playback.play()
        self.core.playback.pause()
        self.core.playback.seek(59123)
        result = dict(status.status(self.context))
        self.assertIn('elapsed', result)
        self.assertEqual(result['elapsed'], '59.123')

    def test_status_method_when_starting_playing_contains_elapsed_zero(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=10000)])
        self.core.playback.play()
        self.core.playback.pause()
        result = dict(status.status(self.context))
        self.assertIn('elapsed', result)
        self.assertEqual(result['elapsed'], '0.000')

    def test_status_method_when_playing_contains_bitrate(self):
        self.core.tracklist.add([Track(uri='dummy:a', bitrate=320)])
        self.core.playback.play()
        result = dict(status.status(self.context))
        self.assertIn('bitrate', result)
        self.assertEqual(int(result['bitrate']), 320)
