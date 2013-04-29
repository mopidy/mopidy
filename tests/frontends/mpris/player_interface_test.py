from __future__ import unicode_literals

import mock
import unittest

import pykka

try:
    import dbus
except ImportError:
    dbus = False

from mopidy import core
from mopidy.backends import dummy
from mopidy.core import PlaybackState
from mopidy.models import Album, Artist, Track

if dbus:
    from mopidy.frontends.mpris import objects

PLAYING = PlaybackState.PLAYING
PAUSED = PlaybackState.PAUSED
STOPPED = PlaybackState.STOPPED


@unittest.skipUnless(dbus, 'dbus not found')
class PlayerInterfaceTest(unittest.TestCase):
    def setUp(self):
        objects.MprisObject._connect_to_dbus = mock.Mock()
        self.backend = dummy.create_dummy_backend_proxy()
        self.core = core.Core.start(backends=[self.backend]).proxy()
        self.mpris = objects.MprisObject(config={}, core=self.core)

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_get_playback_status_is_playing_when_playing(self):
        self.core.playback.state = PLAYING
        result = self.mpris.Get(objects.PLAYER_IFACE, 'PlaybackStatus')
        self.assertEqual('Playing', result)

    def test_get_playback_status_is_paused_when_paused(self):
        self.core.playback.state = PAUSED
        result = self.mpris.Get(objects.PLAYER_IFACE, 'PlaybackStatus')
        self.assertEqual('Paused', result)

    def test_get_playback_status_is_stopped_when_stopped(self):
        self.core.playback.state = STOPPED
        result = self.mpris.Get(objects.PLAYER_IFACE, 'PlaybackStatus')
        self.assertEqual('Stopped', result)

    def test_get_loop_status_is_none_when_not_looping(self):
        self.core.playback.repeat = False
        self.core.playback.single = False
        result = self.mpris.Get(objects.PLAYER_IFACE, 'LoopStatus')
        self.assertEqual('None', result)

    def test_get_loop_status_is_track_when_looping_a_single_track(self):
        self.core.playback.repeat = True
        self.core.playback.single = True
        result = self.mpris.Get(objects.PLAYER_IFACE, 'LoopStatus')
        self.assertEqual('Track', result)

    def test_get_loop_status_is_playlist_when_looping_tracklist(self):
        self.core.playback.repeat = True
        self.core.playback.single = False
        result = self.mpris.Get(objects.PLAYER_IFACE, 'LoopStatus')
        self.assertEqual('Playlist', result)

    def test_set_loop_status_is_ignored_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        self.core.playback.repeat = True
        self.core.playback.single = True
        self.mpris.Set(objects.PLAYER_IFACE, 'LoopStatus', 'None')
        self.assertEqual(self.core.playback.repeat.get(), True)
        self.assertEqual(self.core.playback.single.get(), True)

    def test_set_loop_status_to_none_unsets_repeat_and_single(self):
        self.mpris.Set(objects.PLAYER_IFACE, 'LoopStatus', 'None')
        self.assertEqual(self.core.playback.repeat.get(), False)
        self.assertEqual(self.core.playback.single.get(), False)

    def test_set_loop_status_to_track_sets_repeat_and_single(self):
        self.mpris.Set(objects.PLAYER_IFACE, 'LoopStatus', 'Track')
        self.assertEqual(self.core.playback.repeat.get(), True)
        self.assertEqual(self.core.playback.single.get(), True)

    def test_set_loop_status_to_playlists_sets_repeat_and_not_single(self):
        self.mpris.Set(objects.PLAYER_IFACE, 'LoopStatus', 'Playlist')
        self.assertEqual(self.core.playback.repeat.get(), True)
        self.assertEqual(self.core.playback.single.get(), False)

    def test_get_rate_is_greater_or_equal_than_minimum_rate(self):
        rate = self.mpris.Get(objects.PLAYER_IFACE, 'Rate')
        minimum_rate = self.mpris.Get(objects.PLAYER_IFACE, 'MinimumRate')
        self.assertGreaterEqual(rate, minimum_rate)

    def test_get_rate_is_less_or_equal_than_maximum_rate(self):
        rate = self.mpris.Get(objects.PLAYER_IFACE, 'Rate')
        maximum_rate = self.mpris.Get(objects.PLAYER_IFACE, 'MaximumRate')
        self.assertGreaterEqual(rate, maximum_rate)

    def test_set_rate_is_ignored_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.mpris.Set(objects.PLAYER_IFACE, 'Rate', 0)
        self.assertEqual(self.core.playback.state.get(), PLAYING)

    def test_set_rate_to_zero_pauses_playback(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.mpris.Set(objects.PLAYER_IFACE, 'Rate', 0)
        self.assertEqual(self.core.playback.state.get(), PAUSED)

    def test_get_shuffle_returns_true_if_random_is_active(self):
        self.core.playback.random = True
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Shuffle')
        self.assertTrue(result)

    def test_get_shuffle_returns_false_if_random_is_inactive(self):
        self.core.playback.random = False
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Shuffle')
        self.assertFalse(result)

    def test_set_shuffle_is_ignored_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        self.core.playback.random = False
        self.mpris.Set(objects.PLAYER_IFACE, 'Shuffle', True)
        self.assertFalse(self.core.playback.random.get())

    def test_set_shuffle_to_true_activates_random_mode(self):
        self.core.playback.random = False
        self.assertFalse(self.core.playback.random.get())
        self.mpris.Set(objects.PLAYER_IFACE, 'Shuffle', True)
        self.assertTrue(self.core.playback.random.get())

    def test_set_shuffle_to_false_deactivates_random_mode(self):
        self.core.playback.random = True
        self.assertTrue(self.core.playback.random.get())
        self.mpris.Set(objects.PLAYER_IFACE, 'Shuffle', False)
        self.assertFalse(self.core.playback.random.get())

    def test_get_metadata_has_trackid_even_when_no_current_track(self):
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Metadata')
        self.assertIn('mpris:trackid', result.keys())
        self.assertEqual(result['mpris:trackid'], '')

    def test_get_metadata_has_trackid_based_on_tlid(self):
        self.core.tracklist.add([Track(uri='dummy:a')])
        self.core.playback.play()
        (tlid, track) = self.core.playback.current_tl_track.get()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Metadata')
        self.assertIn('mpris:trackid', result.keys())
        self.assertEqual(
            result['mpris:trackid'], '/com/mopidy/track/%d' % tlid)

    def test_get_metadata_has_track_length(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.play()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Metadata')
        self.assertIn('mpris:length', result.keys())
        self.assertEqual(result['mpris:length'], 40000000)

    def test_get_metadata_has_track_uri(self):
        self.core.tracklist.add([Track(uri='dummy:a')])
        self.core.playback.play()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Metadata')
        self.assertIn('xesam:url', result.keys())
        self.assertEqual(result['xesam:url'], 'dummy:a')

    def test_get_metadata_has_track_title(self):
        self.core.tracklist.add([Track(name='a')])
        self.core.playback.play()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Metadata')
        self.assertIn('xesam:title', result.keys())
        self.assertEqual(result['xesam:title'], 'a')

    def test_get_metadata_has_track_artists(self):
        self.core.tracklist.add([Track(artists=[
            Artist(name='a'), Artist(name='b'), Artist(name=None)])])
        self.core.playback.play()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Metadata')
        self.assertIn('xesam:artist', result.keys())
        self.assertEqual(result['xesam:artist'], ['a', 'b'])

    def test_get_metadata_has_track_album(self):
        self.core.tracklist.add([Track(album=Album(name='a'))])
        self.core.playback.play()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Metadata')
        self.assertIn('xesam:album', result.keys())
        self.assertEqual(result['xesam:album'], 'a')

    def test_get_metadata_has_track_album_artists(self):
        self.core.tracklist.add([Track(album=Album(artists=[
            Artist(name='a'), Artist(name='b'), Artist(name=None)]))])
        self.core.playback.play()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Metadata')
        self.assertIn('xesam:albumArtist', result.keys())
        self.assertEqual(result['xesam:albumArtist'], ['a', 'b'])

    def test_get_metadata_use_first_album_image_as_art_url(self):
        # XXX Currently, the album image order isn't preserved because they
        # are stored as a frozenset(). We pick the first in the set, which is
        # sorted alphabetically, thus we get 'bar.jpg', not 'foo.jpg', which
        # would probably make more sense.
        self.core.tracklist.add([Track(album=Album(images=[
            'http://example.com/foo.jpg', 'http://example.com/bar.jpg']))])
        self.core.playback.play()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Metadata')
        self.assertIn('mpris:artUrl', result.keys())
        self.assertEqual(result['mpris:artUrl'], 'http://example.com/bar.jpg')

    def test_get_metadata_has_no_art_url_if_no_album(self):
        self.core.tracklist.add([Track()])
        self.core.playback.play()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Metadata')
        self.assertNotIn('mpris:artUrl', result.keys())

    def test_get_metadata_has_no_art_url_if_no_album_images(self):
        self.core.tracklist.add([Track(Album(images=[]))])
        self.core.playback.play()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Metadata')
        self.assertNotIn('mpris:artUrl', result.keys())

    def test_get_metadata_has_disc_number_in_album(self):
        self.core.tracklist.add([Track(disc_no=2)])
        self.core.playback.play()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Metadata')
        self.assertIn('xesam:discNumber', result.keys())
        self.assertEqual(result['xesam:discNumber'], 2)

    def test_get_metadata_has_track_number_in_album(self):
        self.core.tracklist.add([Track(track_no=7)])
        self.core.playback.play()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Metadata')
        self.assertIn('xesam:trackNumber', result.keys())
        self.assertEqual(result['xesam:trackNumber'], 7)

    def test_get_volume_should_return_volume_between_zero_and_one(self):
        self.core.playback.volume = None
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Volume')
        self.assertEqual(result, 0)

        self.core.playback.volume = 0
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Volume')
        self.assertEqual(result, 0)

        self.core.playback.volume = 50
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Volume')
        self.assertEqual(result, 0.5)

        self.core.playback.volume = 100
        result = self.mpris.Get(objects.PLAYER_IFACE, 'Volume')
        self.assertEqual(result, 1)

    def test_set_volume_is_ignored_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        self.core.playback.volume = 0
        self.mpris.Set(objects.PLAYER_IFACE, 'Volume', 1.0)
        self.assertEqual(self.core.playback.volume.get(), 0)

    def test_set_volume_to_one_should_set_mixer_volume_to_100(self):
        self.mpris.Set(objects.PLAYER_IFACE, 'Volume', 1.0)
        self.assertEqual(self.core.playback.volume.get(), 100)

    def test_set_volume_to_anything_above_one_sets_mixer_volume_to_100(self):
        self.mpris.Set(objects.PLAYER_IFACE, 'Volume', 2.0)
        self.assertEqual(self.core.playback.volume.get(), 100)

    def test_set_volume_to_anything_not_a_number_does_not_change_volume(self):
        self.core.playback.volume = 10
        self.mpris.Set(objects.PLAYER_IFACE, 'Volume', None)
        self.assertEqual(self.core.playback.volume.get(), 10)

    def test_get_position_returns_time_position_in_microseconds(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.play()
        self.core.playback.seek(10000)
        result_in_microseconds = self.mpris.Get(
            objects.PLAYER_IFACE, 'Position')
        result_in_milliseconds = result_in_microseconds // 1000
        self.assertGreaterEqual(result_in_milliseconds, 10000)

    def test_get_position_when_no_current_track_should_be_zero(self):
        result_in_microseconds = self.mpris.Get(
            objects.PLAYER_IFACE, 'Position')
        result_in_milliseconds = result_in_microseconds // 1000
        self.assertEqual(result_in_milliseconds, 0)

    def test_get_minimum_rate_is_one_or_less(self):
        result = self.mpris.Get(objects.PLAYER_IFACE, 'MinimumRate')
        self.assertLessEqual(result, 1.0)

    def test_get_maximum_rate_is_one_or_more(self):
        result = self.mpris.Get(objects.PLAYER_IFACE, 'MaximumRate')
        self.assertGreaterEqual(result, 1.0)

    def test_can_go_next_is_true_if_can_control_and_other_next_track(self):
        self.mpris.get_CanControl = lambda *_: True
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'CanGoNext')
        self.assertTrue(result)

    def test_can_go_next_is_false_if_next_track_is_the_same(self):
        self.mpris.get_CanControl = lambda *_: True
        self.core.tracklist.add([Track(uri='dummy:a')])
        self.core.playback.repeat = True
        self.core.playback.play()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'CanGoNext')
        self.assertFalse(result)

    def test_can_go_next_is_false_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'CanGoNext')
        self.assertFalse(result)

    def test_can_go_previous_is_true_if_can_control_and_previous_track(self):
        self.mpris.get_CanControl = lambda *_: True
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.core.playback.next()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'CanGoPrevious')
        self.assertTrue(result)

    def test_can_go_previous_is_false_if_previous_track_is_the_same(self):
        self.mpris.get_CanControl = lambda *_: True
        self.core.tracklist.add([Track(uri='dummy:a')])
        self.core.playback.repeat = True
        self.core.playback.play()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'CanGoPrevious')
        self.assertFalse(result)

    def test_can_go_previous_is_false_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.core.playback.next()
        result = self.mpris.Get(objects.PLAYER_IFACE, 'CanGoPrevious')
        self.assertFalse(result)

    def test_can_play_is_true_if_can_control_and_current_track(self):
        self.mpris.get_CanControl = lambda *_: True
        self.core.tracklist.add([Track(uri='dummy:a')])
        self.core.playback.play()
        self.assertTrue(self.core.playback.current_track.get())
        result = self.mpris.Get(objects.PLAYER_IFACE, 'CanPlay')
        self.assertTrue(result)

    def test_can_play_is_false_if_no_current_track(self):
        self.mpris.get_CanControl = lambda *_: True
        self.assertFalse(self.core.playback.current_track.get())
        result = self.mpris.Get(objects.PLAYER_IFACE, 'CanPlay')
        self.assertFalse(result)

    def test_can_play_if_false_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        result = self.mpris.Get(objects.PLAYER_IFACE, 'CanPlay')
        self.assertFalse(result)

    def test_can_pause_is_true_if_can_control_and_track_can_be_paused(self):
        self.mpris.get_CanControl = lambda *_: True
        result = self.mpris.Get(objects.PLAYER_IFACE, 'CanPause')
        self.assertTrue(result)

    def test_can_pause_if_false_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        result = self.mpris.Get(objects.PLAYER_IFACE, 'CanPause')
        self.assertFalse(result)

    def test_can_seek_is_true_if_can_control_is_true(self):
        self.mpris.get_CanControl = lambda *_: True
        result = self.mpris.Get(objects.PLAYER_IFACE, 'CanSeek')
        self.assertTrue(result)

    def test_can_seek_is_false_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        result = self.mpris.Get(objects.PLAYER_IFACE, 'CanSeek')
        self.assertFalse(result)

    def test_can_control_is_true(self):
        result = self.mpris.Get(objects.PLAYER_IFACE, 'CanControl')
        self.assertTrue(result)

    def test_next_is_ignored_if_can_go_next_is_false(self):
        self.mpris.get_CanGoNext = lambda *_: False
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')
        self.mpris.Next()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')

    def test_next_when_playing_skips_to_next_track_and_keep_playing(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.mpris.Next()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:b')
        self.assertEqual(self.core.playback.state.get(), PLAYING)

    def test_next_when_at_end_of_list_should_stop_playback(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.core.playback.next()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:b')
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.mpris.Next()
        self.assertEqual(self.core.playback.state.get(), STOPPED)

    def test_next_when_paused_should_skip_to_next_track_and_stay_paused(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.core.playback.pause()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')
        self.assertEqual(self.core.playback.state.get(), PAUSED)
        self.mpris.Next()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:b')
        self.assertEqual(self.core.playback.state.get(), PAUSED)

    def test_next_when_stopped_skips_to_next_track_and_stay_stopped(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.core.playback.stop()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')
        self.assertEqual(self.core.playback.state.get(), STOPPED)
        self.mpris.Next()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:b')
        self.assertEqual(self.core.playback.state.get(), STOPPED)

    def test_previous_is_ignored_if_can_go_previous_is_false(self):
        self.mpris.get_CanGoPrevious = lambda *_: False
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.core.playback.next()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:b')
        self.mpris.Previous()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:b')

    def test_previous_when_playing_skips_to_prev_track_and_keep_playing(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.core.playback.next()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:b')
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.mpris.Previous()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')
        self.assertEqual(self.core.playback.state.get(), PLAYING)

    def test_previous_when_at_start_of_list_should_stop_playback(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.mpris.Previous()
        self.assertEqual(self.core.playback.state.get(), STOPPED)

    def test_previous_when_paused_skips_to_previous_track_and_pause(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.core.playback.next()
        self.core.playback.pause()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:b')
        self.assertEqual(self.core.playback.state.get(), PAUSED)
        self.mpris.Previous()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')
        self.assertEqual(self.core.playback.state.get(), PAUSED)

    def test_previous_when_stopped_skips_to_previous_track_and_stops(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.core.playback.next()
        self.core.playback.stop()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:b')
        self.assertEqual(self.core.playback.state.get(), STOPPED)
        self.mpris.Previous()
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')
        self.assertEqual(self.core.playback.state.get(), STOPPED)

    def test_pause_is_ignored_if_can_pause_is_false(self):
        self.mpris.get_CanPause = lambda *_: False
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.mpris.Pause()
        self.assertEqual(self.core.playback.state.get(), PLAYING)

    def test_pause_when_playing_should_pause_playback(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.mpris.Pause()
        self.assertEqual(self.core.playback.state.get(), PAUSED)

    def test_pause_when_paused_has_no_effect(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.core.playback.pause()
        self.assertEqual(self.core.playback.state.get(), PAUSED)
        self.mpris.Pause()
        self.assertEqual(self.core.playback.state.get(), PAUSED)

    def test_playpause_is_ignored_if_can_pause_is_false(self):
        self.mpris.get_CanPause = lambda *_: False
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.mpris.PlayPause()
        self.assertEqual(self.core.playback.state.get(), PLAYING)

    def test_playpause_when_playing_should_pause_playback(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.mpris.PlayPause()
        self.assertEqual(self.core.playback.state.get(), PAUSED)

    def test_playpause_when_paused_should_resume_playback(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.core.playback.pause()

        self.assertEqual(self.core.playback.state.get(), PAUSED)
        at_pause = self.core.playback.time_position.get()
        self.assertGreaterEqual(at_pause, 0)

        self.mpris.PlayPause()

        self.assertEqual(self.core.playback.state.get(), PLAYING)
        after_pause = self.core.playback.time_position.get()
        self.assertGreaterEqual(after_pause, at_pause)

    def test_playpause_when_stopped_should_start_playback(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.assertEqual(self.core.playback.state.get(), STOPPED)
        self.mpris.PlayPause()
        self.assertEqual(self.core.playback.state.get(), PLAYING)

    def test_stop_is_ignored_if_can_control_is_false(self):
        self.mpris.get_CanControl = lambda *_: False
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.mpris.Stop()
        self.assertEqual(self.core.playback.state.get(), PLAYING)

    def test_stop_when_playing_should_stop_playback(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.mpris.Stop()
        self.assertEqual(self.core.playback.state.get(), STOPPED)

    def test_stop_when_paused_should_stop_playback(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.core.playback.pause()
        self.assertEqual(self.core.playback.state.get(), PAUSED)
        self.mpris.Stop()
        self.assertEqual(self.core.playback.state.get(), STOPPED)

    def test_play_is_ignored_if_can_play_is_false(self):
        self.mpris.get_CanPlay = lambda *_: False
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.assertEqual(self.core.playback.state.get(), STOPPED)
        self.mpris.Play()
        self.assertEqual(self.core.playback.state.get(), STOPPED)

    def test_play_when_stopped_starts_playback(self):
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.assertEqual(self.core.playback.state.get(), STOPPED)
        self.mpris.Play()
        self.assertEqual(self.core.playback.state.get(), PLAYING)

    def test_play_after_pause_resumes_from_same_position(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.play()

        before_pause = self.core.playback.time_position.get()
        self.assertGreaterEqual(before_pause, 0)

        self.mpris.Pause()
        self.assertEqual(self.core.playback.state.get(), PAUSED)
        at_pause = self.core.playback.time_position.get()
        self.assertGreaterEqual(at_pause, before_pause)

        self.mpris.Play()
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        after_pause = self.core.playback.time_position.get()
        self.assertGreaterEqual(after_pause, at_pause)

    def test_play_when_there_is_no_track_has_no_effect(self):
        self.core.tracklist.clear()
        self.assertEqual(self.core.playback.state.get(), STOPPED)
        self.mpris.Play()
        self.assertEqual(self.core.playback.state.get(), STOPPED)

    def test_seek_is_ignored_if_can_seek_is_false(self):
        self.mpris.get_CanSeek = lambda *_: False
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.play()

        before_seek = self.core.playback.time_position.get()
        self.assertGreaterEqual(before_seek, 0)

        milliseconds_to_seek = 10000
        microseconds_to_seek = milliseconds_to_seek * 1000

        self.mpris.Seek(microseconds_to_seek)

        after_seek = self.core.playback.time_position.get()
        self.assertLessEqual(before_seek, after_seek)
        self.assertLess(after_seek, before_seek + milliseconds_to_seek)

    def test_seek_seeks_given_microseconds_forward_in_the_current_track(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.play()

        before_seek = self.core.playback.time_position.get()
        self.assertGreaterEqual(before_seek, 0)

        milliseconds_to_seek = 10000
        microseconds_to_seek = milliseconds_to_seek * 1000

        self.mpris.Seek(microseconds_to_seek)

        self.assertEqual(self.core.playback.state.get(), PLAYING)

        after_seek = self.core.playback.time_position.get()
        self.assertGreaterEqual(after_seek, before_seek + milliseconds_to_seek)

    def test_seek_seeks_given_microseconds_backward_if_negative(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.play()
        self.core.playback.seek(20000)

        before_seek = self.core.playback.time_position.get()
        self.assertGreaterEqual(before_seek, 20000)

        milliseconds_to_seek = -10000
        microseconds_to_seek = milliseconds_to_seek * 1000

        self.mpris.Seek(microseconds_to_seek)

        self.assertEqual(self.core.playback.state.get(), PLAYING)

        after_seek = self.core.playback.time_position.get()
        self.assertGreaterEqual(after_seek, before_seek + milliseconds_to_seek)
        self.assertLess(after_seek, before_seek)

    def test_seek_seeks_to_start_of_track_if_new_position_is_negative(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.play()
        self.core.playback.seek(20000)

        before_seek = self.core.playback.time_position.get()
        self.assertGreaterEqual(before_seek, 20000)

        milliseconds_to_seek = -30000
        microseconds_to_seek = milliseconds_to_seek * 1000

        self.mpris.Seek(microseconds_to_seek)

        self.assertEqual(self.core.playback.state.get(), PLAYING)

        after_seek = self.core.playback.time_position.get()
        self.assertGreaterEqual(after_seek, before_seek + milliseconds_to_seek)
        self.assertLess(after_seek, before_seek)
        self.assertGreaterEqual(after_seek, 0)

    def test_seek_skips_to_next_track_if_new_position_gt_track_length(self):
        self.core.tracklist.add([
            Track(uri='dummy:a', length=40000),
            Track(uri='dummy:b')])
        self.core.playback.play()
        self.core.playback.seek(20000)

        before_seek = self.core.playback.time_position.get()
        self.assertGreaterEqual(before_seek, 20000)
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')

        milliseconds_to_seek = 50000
        microseconds_to_seek = milliseconds_to_seek * 1000

        self.mpris.Seek(microseconds_to_seek)

        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:b')

        after_seek = self.core.playback.time_position.get()
        self.assertGreaterEqual(after_seek, 0)
        self.assertLess(after_seek, before_seek)

    def test_set_position_is_ignored_if_can_seek_is_false(self):
        self.mpris.get_CanSeek = lambda *_: False
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.play()

        before_set_position = self.core.playback.time_position.get()
        self.assertLessEqual(before_set_position, 5000)

        track_id = 'a'

        position_to_set_in_millisec = 20000
        position_to_set_in_microsec = position_to_set_in_millisec * 1000

        self.mpris.SetPosition(track_id, position_to_set_in_microsec)

        after_set_position = self.core.playback.time_position.get()
        self.assertLessEqual(before_set_position, after_set_position)
        self.assertLess(after_set_position, position_to_set_in_millisec)

    def test_set_position_sets_the_current_track_position_in_microsecs(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.play()

        before_set_position = self.core.playback.time_position.get()
        self.assertLessEqual(before_set_position, 5000)
        self.assertEqual(self.core.playback.state.get(), PLAYING)

        track_id = '/com/mopidy/track/0'

        position_to_set_in_millisec = 20000
        position_to_set_in_microsec = position_to_set_in_millisec * 1000

        self.mpris.SetPosition(track_id, position_to_set_in_microsec)

        self.assertEqual(self.core.playback.state.get(), PLAYING)

        after_set_position = self.core.playback.time_position.get()
        self.assertGreaterEqual(
            after_set_position, position_to_set_in_millisec)

    def test_set_position_does_nothing_if_the_position_is_negative(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.play()
        self.core.playback.seek(20000)

        before_set_position = self.core.playback.time_position.get()
        self.assertGreaterEqual(before_set_position, 20000)
        self.assertLessEqual(before_set_position, 25000)
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')

        track_id = '/com/mopidy/track/0'

        position_to_set_in_millisec = -1000
        position_to_set_in_microsec = position_to_set_in_millisec * 1000

        self.mpris.SetPosition(track_id, position_to_set_in_microsec)

        after_set_position = self.core.playback.time_position.get()
        self.assertGreaterEqual(after_set_position, before_set_position)
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')

    def test_set_position_does_nothing_if_position_is_gt_track_length(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.play()
        self.core.playback.seek(20000)

        before_set_position = self.core.playback.time_position.get()
        self.assertGreaterEqual(before_set_position, 20000)
        self.assertLessEqual(before_set_position, 25000)
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')

        track_id = 'a'

        position_to_set_in_millisec = 50000
        position_to_set_in_microsec = position_to_set_in_millisec * 1000

        self.mpris.SetPosition(track_id, position_to_set_in_microsec)

        after_set_position = self.core.playback.time_position.get()
        self.assertGreaterEqual(after_set_position, before_set_position)
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')

    def test_set_position_is_noop_if_track_id_isnt_current_track(self):
        self.core.tracklist.add([Track(uri='dummy:a', length=40000)])
        self.core.playback.play()
        self.core.playback.seek(20000)

        before_set_position = self.core.playback.time_position.get()
        self.assertGreaterEqual(before_set_position, 20000)
        self.assertLessEqual(before_set_position, 25000)
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')

        track_id = 'b'

        position_to_set_in_millisec = 0
        position_to_set_in_microsec = position_to_set_in_millisec * 1000

        self.mpris.SetPosition(track_id, position_to_set_in_microsec)

        after_set_position = self.core.playback.time_position.get()
        self.assertGreaterEqual(after_set_position, before_set_position)
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')

    def test_open_uri_is_ignored_if_can_play_is_false(self):
        self.mpris.get_CanPlay = lambda *_: False
        self.backend.library.dummy_library = [
            Track(uri='dummy:/test/uri')]
        self.mpris.OpenUri('dummy:/test/uri')
        self.assertEqual(len(self.core.tracklist.tracks.get()), 0)

    def test_open_uri_ignores_uris_with_unknown_uri_scheme(self):
        self.assertListEqual(self.core.uri_schemes.get(), ['dummy'])
        self.mpris.get_CanPlay = lambda *_: True
        self.backend.library.dummy_library = [Track(uri='notdummy:/test/uri')]
        self.mpris.OpenUri('notdummy:/test/uri')
        self.assertEqual(len(self.core.tracklist.tracks.get()), 0)

    def test_open_uri_adds_uri_to_tracklist(self):
        self.mpris.get_CanPlay = lambda *_: True
        self.backend.library.dummy_library = [Track(uri='dummy:/test/uri')]
        self.mpris.OpenUri('dummy:/test/uri')
        self.assertEqual(
            self.core.tracklist.tracks.get()[0].uri, 'dummy:/test/uri')

    def test_open_uri_starts_playback_of_new_track_if_stopped(self):
        self.mpris.get_CanPlay = lambda *_: True
        self.backend.library.dummy_library = [Track(uri='dummy:/test/uri')]
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.assertEqual(self.core.playback.state.get(), STOPPED)

        self.mpris.OpenUri('dummy:/test/uri')

        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.assertEqual(
            self.core.playback.current_track.get().uri, 'dummy:/test/uri')

    def test_open_uri_starts_playback_of_new_track_if_paused(self):
        self.mpris.get_CanPlay = lambda *_: True
        self.backend.library.dummy_library = [Track(uri='dummy:/test/uri')]
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.core.playback.pause()
        self.assertEqual(self.core.playback.state.get(), PAUSED)
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')

        self.mpris.OpenUri('dummy:/test/uri')

        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.assertEqual(
            self.core.playback.current_track.get().uri, 'dummy:/test/uri')

    def test_open_uri_starts_playback_of_new_track_if_playing(self):
        self.mpris.get_CanPlay = lambda *_: True
        self.backend.library.dummy_library = [Track(uri='dummy:/test/uri')]
        self.core.tracklist.add([Track(uri='dummy:a'), Track(uri='dummy:b')])
        self.core.playback.play()
        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.assertEqual(self.core.playback.current_track.get().uri, 'dummy:a')

        self.mpris.OpenUri('dummy:/test/uri')

        self.assertEqual(self.core.playback.state.get(), PLAYING)
        self.assertEqual(
            self.core.playback.current_track.get().uri, 'dummy:/test/uri')
