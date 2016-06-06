from __future__ import absolute_import, unicode_literals

import unittest

import pykka

from mopidy import core
from mopidy.core import PlaybackState
from mopidy.internal import deprecation
from mopidy.models import Track
from mopidy.mpd import dispatcher
from mopidy.mpd.protocol import status

from tests import dummy_audio, dummy_backend, dummy_mixer


PAUSED = PlaybackState.PAUSED
PLAYING = PlaybackState.PLAYING
STOPPED = PlaybackState.STOPPED

# FIXME migrate to using protocol.BaseTestCase instead of status.stats
# directly?


class StatusHandlerTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        config = {
            'core': {
                'max_tracklist_length': 10000,
            }
        }

        self.audio = dummy_audio.create_proxy()
        self.mixer = dummy_mixer.create_proxy()
        self.backend = dummy_backend.create_proxy(audio=self.audio)

        with deprecation.ignore():
            self.core = core.Core.start(
                config,
                audio=self.audio,
                mixer=self.mixer,
                backends=[self.backend]).proxy()

        self.dispatcher = dispatcher.MpdDispatcher(core=self.core)
        self.context = self.dispatcher.context

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()

    def set_tracklist(self, tracks):
        self.backend.library.dummy_library = tracks
        self.core.tracklist.add(uris=[track.uri for track in tracks]).get()

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
        self.core.mixer.set_volume(17)
        result = dict(status.status(self.context))
        self.assertIn('volume', result)
        self.assertEqual(int(result['volume']), 17)

    def test_status_method_contains_repeat_is_0(self):
        result = dict(status.status(self.context))
        self.assertIn('repeat', result)
        self.assertEqual(int(result['repeat']), 0)

    def test_status_method_contains_repeat_is_1(self):
        self.core.tracklist.set_repeat(True)
        result = dict(status.status(self.context))
        self.assertIn('repeat', result)
        self.assertEqual(int(result['repeat']), 1)

    def test_status_method_contains_random_is_0(self):
        result = dict(status.status(self.context))
        self.assertIn('random', result)
        self.assertEqual(int(result['random']), 0)

    def test_status_method_contains_random_is_1(self):
        self.core.tracklist.set_random(True)
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
        self.core.tracklist.set_consume(True)
        result = dict(status.status(self.context))
        self.assertIn('consume', result)
        self.assertEqual(int(result['consume']), 1)

    def test_status_method_contains_playlist(self):
        result = dict(status.status(self.context))
        self.assertIn('playlist', result)
        self.assertGreaterEqual(int(result['playlist']), 0)
        self.assertLessEqual(int(result['playlist']), 2 ** 31 - 1)

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
        self.set_tracklist([Track(uri='dummy:/a')])
        self.core.playback.play().get()
        result = dict(status.status(self.context))
        self.assertIn('song', result)
        self.assertGreaterEqual(int(result['song']), 0)

    def test_status_method_when_playlist_loaded_contains_tlid_as_songid(self):
        self.set_tracklist([Track(uri='dummy:/a')])
        self.core.playback.play().get()
        result = dict(status.status(self.context))
        self.assertIn('songid', result)
        self.assertEqual(int(result['songid']), 1)

    def test_status_method_when_playlist_loaded_contains_nextsong(self):
        self.set_tracklist([Track(uri='dummy:/a'), Track(uri='dummy:/b')])
        self.core.playback.play().get()
        result = dict(status.status(self.context))
        self.assertIn('nextsong', result)
        self.assertGreaterEqual(int(result['nextsong']), 0)

    def test_status_method_when_playlist_loaded_contains_nextsongid(self):
        self.set_tracklist([Track(uri='dummy:/a'), Track(uri='dummy:/b')])
        self.core.playback.play().get()
        result = dict(status.status(self.context))
        self.assertIn('nextsongid', result)
        self.assertEqual(int(result['nextsongid']), 2)

    def test_status_method_when_playing_contains_time_with_no_length(self):
        self.set_tracklist([Track(uri='dummy:/a', length=None)])
        self.core.playback.play().get()
        result = dict(status.status(self.context))
        self.assertIn('time', result)
        (position, total) = result['time'].split(':')
        position = int(position)
        total = int(total)
        self.assertLessEqual(position, total)

    def test_status_method_when_playing_contains_time_with_length(self):
        self.set_tracklist([Track(uri='dummy:/a', length=10000)])
        self.core.playback.play()
        result = dict(status.status(self.context))
        self.assertIn('time', result)
        (position, total) = result['time'].split(':')
        position = int(position)
        total = int(total)
        self.assertLessEqual(position, total)

    def test_status_method_when_playing_contains_elapsed(self):
        self.set_tracklist([Track(uri='dummy:/a', length=60000)])
        self.core.playback.play().get()
        self.core.playback.pause()
        self.core.playback.seek(59123)
        result = dict(status.status(self.context))
        self.assertIn('elapsed', result)
        self.assertEqual(result['elapsed'], '59.123')

    def test_status_method_when_starting_playing_contains_elapsed_zero(self):
        self.set_tracklist([Track(uri='dummy:/a', length=10000)])
        self.core.playback.play().get()
        self.core.playback.pause()
        result = dict(status.status(self.context))
        self.assertIn('elapsed', result)
        self.assertEqual(result['elapsed'], '0.000')

    def test_status_method_when_playing_contains_bitrate(self):
        self.set_tracklist([Track(uri='dummy:/a', bitrate=3200)])
        self.core.playback.play().get()
        result = dict(status.status(self.context))
        self.assertIn('bitrate', result)
        self.assertEqual(int(result['bitrate']), 3200)
