from __future__ import unicode_literals

import mock

from mopidy.core import CoreListener, PlaybackState
from mopidy.models import Playlist, Track

from tests import unittest


class CoreListenerTest(unittest.TestCase):
    def setUp(self):
        self.listener = CoreListener()

    def test_on_event_forwards_to_specific_handler(self):
        self.listener.track_playback_paused = mock.Mock()

        self.listener.on_event(
            'track_playback_paused', track=Track(), position=0)

        self.listener.track_playback_paused.assert_called_with(
            track=Track(), position=0)

    def test_listener_has_default_impl_for_track_playback_paused(self):
        self.listener.track_playback_paused(Track(), 0)

    def test_listener_has_default_impl_for_track_playback_resumed(self):
        self.listener.track_playback_resumed(Track(), 0)

    def test_listener_has_default_impl_for_track_playback_started(self):
        self.listener.track_playback_started(Track())

    def test_listener_has_default_impl_for_track_playback_ended(self):
        self.listener.track_playback_ended(Track(), 0)

    def test_listener_has_default_impl_for_playback_state_changed(self):
        self.listener.playback_state_changed(
            PlaybackState.STOPPED, PlaybackState.PLAYING)

    def test_listener_has_default_impl_for_tracklist_changed(self):
        self.listener.tracklist_changed()

    def test_listener_has_default_impl_for_playlists_loaded(self):
        self.listener.playlists_loaded()

    def test_listener_has_default_impl_for_playlist_changed(self):
        self.listener.playlist_changed(Playlist())

    def test_listener_has_default_impl_for_options_changed(self):
        self.listener.options_changed()

    def test_listener_has_default_impl_for_volume_changed(self):
        self.listener.volume_changed()

    def test_listener_has_default_impl_for_seeked(self):
        self.listener.seeked(0)
