from __future__ import absolute_import, unicode_literals

import unittest

from mopidy.core import PlaybackState
from mopidy.internal import deprecation
from mopidy.models import Track

from tests.mpd import protocol


PAUSED = PlaybackState.PAUSED
PLAYING = PlaybackState.PLAYING
STOPPED = PlaybackState.STOPPED


class PlaybackOptionsHandlerTest(protocol.BaseTestCase):

    def test_consume_off(self):
        self.send_request('consume "0"')
        self.assertFalse(self.core.tracklist.consume.get())
        self.assertInResponse('OK')

    def test_consume_off_without_quotes(self):
        self.send_request('consume 0')
        self.assertFalse(self.core.tracklist.consume.get())
        self.assertInResponse('OK')

    def test_consume_on(self):
        self.send_request('consume "1"')
        self.assertTrue(self.core.tracklist.consume.get())
        self.assertInResponse('OK')

    def test_consume_on_without_quotes(self):
        self.send_request('consume 1')
        self.assertTrue(self.core.tracklist.consume.get())
        self.assertInResponse('OK')

    def test_crossfade(self):
        self.send_request('crossfade "10"')
        self.assertInResponse('ACK [0@0] {crossfade} Not implemented')

    def test_random_off(self):
        self.send_request('random "0"')
        self.assertFalse(self.core.tracklist.random.get())
        self.assertInResponse('OK')

    def test_random_off_without_quotes(self):
        self.send_request('random 0')
        self.assertFalse(self.core.tracklist.random.get())
        self.assertInResponse('OK')

    def test_random_on(self):
        self.send_request('random "1"')
        self.assertTrue(self.core.tracklist.random.get())
        self.assertInResponse('OK')

    def test_random_on_without_quotes(self):
        self.send_request('random 1')
        self.assertTrue(self.core.tracklist.random.get())
        self.assertInResponse('OK')

    def test_repeat_off(self):
        self.send_request('repeat "0"')
        self.assertFalse(self.core.tracklist.repeat.get())
        self.assertInResponse('OK')

    def test_repeat_off_without_quotes(self):
        self.send_request('repeat 0')
        self.assertFalse(self.core.tracklist.repeat.get())
        self.assertInResponse('OK')

    def test_repeat_on(self):
        self.send_request('repeat "1"')
        self.assertTrue(self.core.tracklist.repeat.get())
        self.assertInResponse('OK')

    def test_repeat_on_without_quotes(self):
        self.send_request('repeat 1')
        self.assertTrue(self.core.tracklist.repeat.get())
        self.assertInResponse('OK')

    def test_single_off(self):
        self.send_request('single "0"')
        self.assertFalse(self.core.tracklist.single.get())
        self.assertInResponse('OK')

    def test_single_off_without_quotes(self):
        self.send_request('single 0')
        self.assertFalse(self.core.tracklist.single.get())
        self.assertInResponse('OK')

    def test_single_on(self):
        self.send_request('single "1"')
        self.assertTrue(self.core.tracklist.single.get())
        self.assertInResponse('OK')

    def test_single_on_without_quotes(self):
        self.send_request('single 1')
        self.assertTrue(self.core.tracklist.single.get())
        self.assertInResponse('OK')

    def test_replay_gain_mode_off(self):
        self.send_request('replay_gain_mode "off"')
        self.assertInResponse('ACK [0@0] {replay_gain_mode} Not implemented')

    def test_replay_gain_mode_track(self):
        self.send_request('replay_gain_mode "track"')
        self.assertInResponse('ACK [0@0] {replay_gain_mode} Not implemented')

    def test_replay_gain_mode_album(self):
        self.send_request('replay_gain_mode "album"')
        self.assertInResponse('ACK [0@0] {replay_gain_mode} Not implemented')

    def test_replay_gain_status_default(self):
        self.send_request('replay_gain_status')
        self.assertInResponse('OK')
        self.assertInResponse('replay_gain_mode: off')

    def test_mixrampdb(self):
        self.send_request('mixrampdb "10"')
        self.assertInResponse('ACK [0@0] {mixrampdb} Not implemented')

    def test_mixrampdelay(self):
        self.send_request('mixrampdelay "10"')
        self.assertInResponse('ACK [0@0] {mixrampdelay} Not implemented')

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

    def setUp(self):  # noqa: N802
        super(PlaybackControlHandlerTest, self).setUp()
        self.tracks = [Track(uri='dummy:a', length=40000),
                       Track(uri='dummy:b', length=40000)]
        self.backend.library.dummy_library = self.tracks
        self.core.tracklist.add(uris=[t.uri for t in self.tracks]).get()

    def test_next(self):
        self.core.tracklist.clear().get()
        self.send_request('next')
        self.assertInResponse('OK')

    def test_pause_off(self):
        self.send_request('play "0"')
        self.send_request('pause "1"')
        self.send_request('pause "0"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse('OK')

    def test_pause_on(self):
        self.send_request('play "0"')
        self.send_request('pause "1"')
        self.assertEqual(PAUSED, self.core.playback.state.get())
        self.assertInResponse('OK')

    def test_pause_toggle(self):
        self.send_request('play "0"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse('OK')

        with deprecation.ignore('mpd.protocol.playback.pause:state_arg'):
            self.send_request('pause')
            self.assertEqual(PAUSED, self.core.playback.state.get())
            self.assertInResponse('OK')

            self.send_request('pause')
            self.assertEqual(PLAYING, self.core.playback.state.get())
            self.assertInResponse('OK')

    def test_play_without_pos(self):
        self.send_request('play')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse('OK')

    def test_play_with_pos(self):
        self.send_request('play "0"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse('OK')

    def test_play_with_pos_without_quotes(self):
        self.send_request('play 0')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse('OK')

    def test_play_with_pos_out_of_bounds(self):
        self.core.tracklist.clear().get()
        self.send_request('play "0"')
        self.assertEqual(STOPPED, self.core.playback.state.get())
        self.assertInResponse('ACK [2@0] {play} Bad song index')

    def test_play_minus_one_plays_first_in_playlist_if_no_current_track(self):
        self.assertEqual(self.core.playback.current_track.get(), None)

        self.send_request('play "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertEqual(
            'dummy:a', self.core.playback.current_track.get().uri)
        self.assertInResponse('OK')

    def test_play_minus_one_plays_current_track_if_current_track_is_set(self):
        self.assertEqual(self.core.playback.current_track.get(), None)
        self.core.playback.play()
        self.core.playback.next()
        self.core.playback.stop().get()
        self.assertNotEqual(self.core.playback.current_track.get(), None)

        self.send_request('play "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertEqual(
            'dummy:b', self.core.playback.current_track.get().uri)
        self.assertInResponse('OK')

    def test_play_minus_one_on_empty_playlist_does_not_ack(self):
        self.core.tracklist.clear()

        self.send_request('play "-1"')
        self.assertEqual(STOPPED, self.core.playback.state.get())
        self.assertEqual(None, self.core.playback.current_track.get())
        self.assertInResponse('OK')

    def test_play_minus_is_ignored_if_playing(self):
        self.core.playback.play().get()
        self.core.playback.seek(30000)
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertEqual(PLAYING, self.core.playback.state.get())

        self.send_request('play "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse('OK')

    def test_play_minus_one_resumes_if_paused(self):
        self.core.playback.play().get()
        self.core.playback.seek(30000)
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.core.playback.pause()
        self.assertEqual(PAUSED, self.core.playback.state.get())

        self.send_request('play "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse('OK')

    def test_playid(self):
        self.send_request('playid "1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse('OK')

    def test_playid_without_quotes(self):
        self.send_request('playid 1')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertInResponse('OK')

    def test_playid_minus_1_plays_first_in_playlist_if_no_current_track(self):
        self.assertEqual(self.core.playback.current_track.get(), None)

        self.send_request('playid "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertEqual(
            'dummy:a', self.core.playback.current_track.get().uri)
        self.assertInResponse('OK')

    def test_playid_minus_1_plays_current_track_if_current_track_is_set(self):
        self.assertEqual(self.core.playback.current_track.get(), None)
        self.core.playback.play().get()
        self.core.playback.next().get()
        self.core.playback.stop()
        self.assertNotEqual(None, self.core.playback.current_track.get())

        self.send_request('playid "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertEqual(
            'dummy:b', self.core.playback.current_track.get().uri)
        self.assertInResponse('OK')

    def test_playid_minus_one_on_empty_playlist_does_not_ack(self):
        self.core.tracklist.clear()

        self.send_request('playid "-1"')
        self.assertEqual(STOPPED, self.core.playback.state.get())
        self.assertEqual(None, self.core.playback.current_track.get())
        self.assertInResponse('OK')

    def test_playid_minus_is_ignored_if_playing(self):
        self.core.playback.play().get()
        self.core.playback.seek(30000)
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertEqual(PLAYING, self.core.playback.state.get())

        self.send_request('playid "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse('OK')

    def test_playid_minus_one_resumes_if_paused(self):
        self.core.playback.play().get()
        self.core.playback.seek(30000)
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.core.playback.pause()
        self.assertEqual(PAUSED, self.core.playback.state.get())

        self.send_request('playid "-1"')
        self.assertEqual(PLAYING, self.core.playback.state.get())
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse('OK')

    def test_playid_which_does_not_exist(self):
        self.send_request('playid "12345"')
        self.assertInResponse('ACK [50@0] {playid} No such song')

    def test_previous(self):
        self.core.tracklist.clear().get()
        self.send_request('previous')
        self.assertInResponse('OK')

    def test_seek_in_current_track(self):
        self.core.playback.play()

        self.send_request('seek "0" "30"')

        current_track = self.core.playback.current_track.get()
        self.assertEqual(current_track, self.tracks[0])
        self.assertGreaterEqual(self.core.playback.time_position, 30000)
        self.assertInResponse('OK')

    def test_seek_in_another_track(self):
        self.core.playback.play()
        current_track = self.core.playback.current_track.get()
        self.assertNotEqual(current_track, self.tracks[1])

        self.send_request('seek "1" "30"')

        current_track = self.core.playback.current_track.get()
        self.assertEqual(current_track, self.tracks[1])
        self.assertInResponse('OK')

    def test_seek_without_quotes(self):
        self.core.playback.play()

        self.send_request('seek 0 30')
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse('OK')

    def test_seekid_in_current_track(self):
        self.core.playback.play()

        self.send_request('seekid "1" "30"')

        current_track = self.core.playback.current_track.get()
        self.assertEqual(current_track, self.tracks[0])
        self.assertGreaterEqual(
            self.core.playback.time_position.get(), 30000)
        self.assertInResponse('OK')

    def test_seekid_in_another_track(self):
        self.core.playback.play()

        self.send_request('seekid "2" "30"')

        current_tl_track = self.core.playback.current_tl_track.get()
        self.assertEqual(current_tl_track.tlid, 2)
        self.assertEqual(current_tl_track.track, self.tracks[1])
        self.assertInResponse('OK')

    def test_seekcur_absolute_value(self):
        self.core.playback.play().get()

        self.send_request('seekcur "30"')

        self.assertGreaterEqual(self.core.playback.time_position.get(), 30000)
        self.assertInResponse('OK')

    def test_seekcur_positive_diff(self):
        self.core.playback.play().get()
        self.core.playback.seek(10000)
        self.assertGreaterEqual(self.core.playback.time_position.get(), 10000)

        self.send_request('seekcur "+20"')

        self.assertGreaterEqual(self.core.playback.time_position.get(), 30000)
        self.assertInResponse('OK')

    def test_seekcur_negative_diff(self):
        self.core.playback.play().get()
        self.core.playback.seek(30000)
        self.assertGreaterEqual(self.core.playback.time_position.get(), 30000)

        self.send_request('seekcur "-20"')

        self.assertLessEqual(self.core.playback.time_position.get(), 15000)
        self.assertInResponse('OK')

    def test_stop(self):
        self.core.tracklist.clear().get()
        self.send_request('stop')
        self.assertEqual(STOPPED, self.core.playback.state.get())
        self.assertInResponse('OK')


class VolumeTest(protocol.BaseTestCase):

    def test_setvol_below_min(self):
        self.send_request('setvol "-10"')
        self.assertEqual(0, self.core.mixer.get_volume().get())
        self.assertInResponse('OK')

    def test_setvol_min(self):
        self.send_request('setvol "0"')
        self.assertEqual(0, self.core.mixer.get_volume().get())
        self.assertInResponse('OK')

    def test_setvol_middle(self):
        self.send_request('setvol "50"')
        self.assertEqual(50, self.core.mixer.get_volume().get())
        self.assertInResponse('OK')

    def test_setvol_max(self):
        self.send_request('setvol "100"')
        self.assertEqual(100, self.core.mixer.get_volume().get())
        self.assertInResponse('OK')

    def test_setvol_above_max(self):
        self.send_request('setvol "110"')
        self.assertEqual(100, self.core.mixer.get_volume().get())
        self.assertInResponse('OK')

    def test_setvol_plus_is_ignored(self):
        self.send_request('setvol "+10"')
        self.assertEqual(10, self.core.mixer.get_volume().get())
        self.assertInResponse('OK')

    def test_setvol_without_quotes(self):
        self.send_request('setvol 50')
        self.assertEqual(50, self.core.mixer.get_volume().get())
        self.assertInResponse('OK')

    def test_volume_plus(self):
        self.core.mixer.set_volume(50)

        self.send_request('volume +20')

        self.assertEqual(70, self.core.mixer.get_volume().get())
        self.assertInResponse('OK')

    def test_volume_minus(self):
        self.core.mixer.set_volume(50)

        self.send_request('volume -20')

        self.assertEqual(30, self.core.mixer.get_volume().get())
        self.assertInResponse('OK')

    def test_volume_less_than_minus_100(self):
        self.core.mixer.set_volume(50)

        self.send_request('volume -110')

        self.assertEqual(50, self.core.mixer.get_volume().get())
        self.assertInResponse('ACK [2@0] {volume} Invalid volume value')

    def test_volume_more_than_plus_100(self):
        self.core.mixer.set_volume(50)

        self.send_request('volume +110')

        self.assertEqual(50, self.core.mixer.get_volume().get())
        self.assertInResponse('ACK [2@0] {volume} Invalid volume value')


class VolumeWithNoMixerTest(protocol.BaseTestCase):
    enable_mixer = False

    def test_setvol_without_mixer_fails(self):
        self.send_request('setvol "100"')
        self.assertInResponse('ACK [52@0] {setvol} problems setting volume')

    def test_volume_without_mixer_failes(self):
        self.send_request('volume +100')
        self.assertInResponse('ACK [52@0] {volume} problems setting volume')
