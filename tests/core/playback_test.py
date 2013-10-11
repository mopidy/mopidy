from __future__ import unicode_literals

import mock
import unittest

from mopidy.backends import base
from mopidy.core import Core, PlaybackState
from mopidy.models import Track


class CorePlaybackTest(unittest.TestCase):
    def setUp(self):
        self.backend1 = mock.Mock()
        self.backend1.uri_schemes.get.return_value = ['dummy1']
        self.playback1 = mock.Mock(spec=base.BasePlaybackProvider)
        self.backend1.playback = self.playback1

        self.backend2 = mock.Mock()
        self.backend2.uri_schemes.get.return_value = ['dummy2']
        self.playback2 = mock.Mock(spec=base.BasePlaybackProvider)
        self.backend2.playback = self.playback2

        # A backend without the optional playback provider
        self.backend3 = mock.Mock()
        self.backend3.uri_schemes.get.return_value = ['dummy3']
        self.backend3.has_playback().get.return_value = False

        self.tracks = [
            Track(uri='dummy1:a', length=40000),
            Track(uri='dummy2:a', length=40000),
            Track(uri='dummy3:a', length=40000),  # Unplayable
            Track(uri='dummy1:b', length=40000),
        ]

        self.core = Core(audio=None, backends=[
            self.backend1, self.backend2, self.backend3])
        self.core.tracklist.add(self.tracks)

        self.tl_tracks = self.core.tracklist.tl_tracks
        self.unplayable_tl_track = self.tl_tracks[2]

    def test_play_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])

        self.playback1.play.assert_called_once_with(self.tracks[0])
        self.assertFalse(self.playback2.play.called)

    def test_play_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])

        self.assertFalse(self.playback1.play.called)
        self.playback2.play.assert_called_once_with(self.tracks[1])

    def test_play_skips_to_next_on_unplayable_track(self):
        self.core.playback.play(self.unplayable_tl_track)

        self.playback1.play.assert_called_once_with(self.tracks[3])
        self.assertFalse(self.playback2.play.called)

        self.assertEqual(
            self.core.playback.current_tl_track, self.tl_tracks[3])

    def test_pause_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])
        self.core.playback.pause()

        self.playback1.pause.assert_called_once_with()
        self.assertFalse(self.playback2.pause.called)

    def test_pause_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])
        self.core.playback.pause()

        self.assertFalse(self.playback1.pause.called)
        self.playback2.pause.assert_called_once_with()

    def test_pause_changes_state_even_if_track_is_unplayable(self):
        self.core.playback.current_tl_track = self.unplayable_tl_track
        self.core.playback.pause()

        self.assertEqual(self.core.playback.state, PlaybackState.PAUSED)
        self.assertFalse(self.playback1.pause.called)
        self.assertFalse(self.playback2.pause.called)

    def test_resume_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])
        self.core.playback.pause()
        self.core.playback.resume()

        self.playback1.resume.assert_called_once_with()
        self.assertFalse(self.playback2.resume.called)

    def test_resume_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])
        self.core.playback.pause()
        self.core.playback.resume()

        self.assertFalse(self.playback1.resume.called)
        self.playback2.resume.assert_called_once_with()

    def test_resume_does_nothing_if_track_is_unplayable(self):
        self.core.playback.current_tl_track = self.unplayable_tl_track
        self.core.playback.state = PlaybackState.PAUSED
        self.core.playback.resume()

        self.assertEqual(self.core.playback.state, PlaybackState.PAUSED)
        self.assertFalse(self.playback1.resume.called)
        self.assertFalse(self.playback2.resume.called)

    def test_stop_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])
        self.core.playback.stop()

        self.playback1.stop.assert_called_once_with()
        self.assertFalse(self.playback2.stop.called)

    def test_stop_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])
        self.core.playback.stop()

        self.assertFalse(self.playback1.stop.called)
        self.playback2.stop.assert_called_once_with()

    def test_stop_changes_state_even_if_track_is_unplayable(self):
        self.core.playback.current_tl_track = self.unplayable_tl_track
        self.core.playback.state = PlaybackState.PAUSED
        self.core.playback.stop()

        self.assertEqual(self.core.playback.state, PlaybackState.STOPPED)
        self.assertFalse(self.playback1.stop.called)
        self.assertFalse(self.playback2.stop.called)

    def test_seek_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])
        self.core.playback.seek(10000)

        self.playback1.seek.assert_called_once_with(10000)
        self.assertFalse(self.playback2.seek.called)

    def test_seek_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])
        self.core.playback.seek(10000)

        self.assertFalse(self.playback1.seek.called)
        self.playback2.seek.assert_called_once_with(10000)

    def test_seek_fails_for_unplayable_track(self):
        self.core.playback.current_tl_track = self.unplayable_tl_track
        self.core.playback.state = PlaybackState.PLAYING
        success = self.core.playback.seek(1000)

        self.assertFalse(success)
        self.assertFalse(self.playback1.seek.called)
        self.assertFalse(self.playback2.seek.called)

    def test_time_position_selects_dummy1_backend(self):
        self.core.playback.play(self.tl_tracks[0])
        self.core.playback.seek(10000)
        self.core.playback.time_position

        self.playback1.get_time_position.assert_called_once_with()
        self.assertFalse(self.playback2.get_time_position.called)

    def test_time_position_selects_dummy2_backend(self):
        self.core.playback.play(self.tl_tracks[1])
        self.core.playback.seek(10000)
        self.core.playback.time_position

        self.assertFalse(self.playback1.get_time_position.called)
        self.playback2.get_time_position.assert_called_once_with()

    def test_time_position_returns_0_if_track_is_unplayable(self):
        self.core.playback.current_tl_track = self.unplayable_tl_track

        result = self.core.playback.time_position

        self.assertEqual(result, 0)
        self.assertFalse(self.playback1.get_time_position.called)
        self.assertFalse(self.playback2.get_time_position.called)

    def test_mute(self):
        self.assertEqual(self.core.playback.mute, False)

        self.core.playback.mute = True

        self.assertEqual(self.core.playback.mute, True)
