from __future__ import absolute_import, unicode_literals

import unittest

import mock

from mopidy.core import CoreListener, PlaybackState
from mopidy.models import Playlist, TlTrack


class CoreListenerTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.listener = CoreListener()

    def test_on_event_forwards_to_specific_handler(self):
        self.listener.track_playback_paused = mock.Mock()

        self.listener.on_event(
            'track_playback_paused', track=TlTrack(), position=0)

        self.listener.track_playback_paused.assert_called_with(
            track=TlTrack(), position=0)

    def test_listener_has_default_impl_for_track_playback_paused(self):
        self.listener.track_playback_paused(TlTrack(), 0)

    def test_listener_has_default_impl_for_track_playback_resumed(self):
        self.listener.track_playback_resumed(TlTrack(), 0)

    def test_listener_has_default_impl_for_track_playback_started(self):
        self.listener.track_playback_started(TlTrack())

    def test_listener_has_default_impl_for_track_playback_ended(self):
        self.listener.track_playback_ended(TlTrack(), 0)

    def test_listener_has_default_impl_for_playback_state_changed(self):
        self.listener.playback_state_changed(
            PlaybackState.STOPPED, PlaybackState.PLAYING)

    def test_listener_has_default_impl_for_tracklist_changed(self):
        self.listener.tracklist_changed()

    def test_listener_has_default_impl_for_playlists_loaded(self):
        self.listener.playlists_loaded()

    def test_listener_has_default_impl_for_playlist_changed(self):
        self.listener.playlist_changed(Playlist())

    def test_listener_has_default_impl_for_playlist_deleted(self):
        self.listener.playlist_deleted(Playlist())

    def test_listener_has_default_impl_for_options_changed(self):
        self.listener.options_changed()

    def test_listener_has_default_impl_for_volume_changed(self):
        self.listener.volume_changed(70)

    def test_listener_has_default_impl_for_mute_changed(self):
        self.listener.mute_changed(True)

    def test_listener_has_default_impl_for_seeked(self):
        self.listener.seeked(0)

    def test_listener_has_default_impl_for_stream_title_changed(self):
        self.listener.stream_title_changed('foobar')
