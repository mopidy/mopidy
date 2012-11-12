from __future__ import unicode_literals

import mock

from mopidy.backends import base
from mopidy.core import Core
from mopidy.models import Track

from tests import unittest


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

        self.tracks = [
            Track(uri='dummy1://foo', length=40000),
            Track(uri='dummy1://bar', length=40000),
            Track(uri='dummy2://foo', length=40000),
            Track(uri='dummy2://bar', length=40000),
        ]

        self.core = Core(audio=None, backends=[self.backend1, self.backend2])
        self.core.current_playlist.append(self.tracks)

        self.cp_tracks = self.core.current_playlist.cp_tracks

    def test_play_selects_dummy1_backend(self):
        self.core.playback.play(self.cp_tracks[0])

        self.playback1.play.assert_called_once_with(self.tracks[0])
        self.assertFalse(self.playback2.play.called)

    def test_play_selects_dummy2_backend(self):
        self.core.playback.play(self.cp_tracks[2])

        self.assertFalse(self.playback1.play.called)
        self.playback2.play.assert_called_once_with(self.tracks[2])

    def test_pause_selects_dummy1_backend(self):
        self.core.playback.play(self.cp_tracks[0])
        self.core.playback.pause()

        self.playback1.pause.assert_called_once_with()
        self.assertFalse(self.playback2.pause.called)

    def test_pause_selects_dummy2_backend(self):
        self.core.playback.play(self.cp_tracks[2])
        self.core.playback.pause()

        self.assertFalse(self.playback1.pause.called)
        self.playback2.pause.assert_called_once_with()

    def test_resume_selects_dummy1_backend(self):
        self.core.playback.play(self.cp_tracks[0])
        self.core.playback.pause()
        self.core.playback.resume()

        self.playback1.resume.assert_called_once_with()
        self.assertFalse(self.playback2.resume.called)

    def test_resume_selects_dummy2_backend(self):
        self.core.playback.play(self.cp_tracks[2])
        self.core.playback.pause()
        self.core.playback.resume()

        self.assertFalse(self.playback1.resume.called)
        self.playback2.resume.assert_called_once_with()

    def test_stop_selects_dummy1_backend(self):
        self.core.playback.play(self.cp_tracks[0])
        self.core.playback.stop()

        self.playback1.stop.assert_called_once_with()
        self.assertFalse(self.playback2.stop.called)

    def test_stop_selects_dummy2_backend(self):
        self.core.playback.play(self.cp_tracks[2])
        self.core.playback.stop()

        self.assertFalse(self.playback1.stop.called)
        self.playback2.stop.assert_called_once_with()

    def test_seek_selects_dummy1_backend(self):
        self.core.playback.play(self.cp_tracks[0])
        self.core.playback.seek(10000)

        self.playback1.seek.assert_called_once_with(10000)
        self.assertFalse(self.playback2.seek.called)

    def test_seek_selects_dummy2_backend(self):
        self.core.playback.play(self.cp_tracks[2])
        self.core.playback.seek(10000)

        self.assertFalse(self.playback1.seek.called)
        self.playback2.seek.assert_called_once_with(10000)

    def test_time_position_selects_dummy1_backend(self):
        self.core.playback.play(self.cp_tracks[0])
        self.core.playback.seek(10000)
        self.core.playback.time_position

        self.playback1.get_time_position.assert_called_once_with()
        self.assertFalse(self.playback2.get_time_position.called)

    def test_time_position_selects_dummy2_backend(self):
        self.core.playback.play(self.cp_tracks[2])
        self.core.playback.seek(10000)
        self.core.playback.time_position

        self.assertFalse(self.playback1.get_time_position.called)
        self.playback2.get_time_position.assert_called_once_with()
