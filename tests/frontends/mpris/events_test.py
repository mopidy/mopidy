from __future__ import unicode_literals

import mock
import unittest

try:
    import dbus
except ImportError:
    dbus = False

from mopidy.models import Playlist, TlTrack

if dbus:
    from mopidy.frontends.mpris import actor, objects


@unittest.skipUnless(dbus, 'dbus not found')
class BackendEventsTest(unittest.TestCase):
    def setUp(self):
        # As a plain class, not an actor:
        self.mpris_frontend = actor.MprisFrontend(config=None, core=None)
        self.mpris_object = mock.Mock(spec=objects.MprisObject)
        self.mpris_frontend.mpris_object = self.mpris_object

    def test_track_playback_paused_event_changes_playback_status(self):
        self.mpris_object.Get.return_value = 'Paused'
        self.mpris_frontend.track_playback_paused(TlTrack(), 0)
        self.assertListEqual(self.mpris_object.Get.call_args_list, [
            ((objects.PLAYER_IFACE, 'PlaybackStatus'), {}),
        ])
        self.mpris_object.PropertiesChanged.assert_called_with(
            objects.PLAYER_IFACE, {'PlaybackStatus': 'Paused'}, [])

    def test_track_playback_resumed_event_changes_playback_status(self):
        self.mpris_object.Get.return_value = 'Playing'
        self.mpris_frontend.track_playback_resumed(TlTrack(), 0)
        self.assertListEqual(self.mpris_object.Get.call_args_list, [
            ((objects.PLAYER_IFACE, 'PlaybackStatus'), {}),
        ])
        self.mpris_object.PropertiesChanged.assert_called_with(
            objects.PLAYER_IFACE, {'PlaybackStatus': 'Playing'}, [])

    def test_track_playback_started_changes_playback_status_and_metadata(self):
        self.mpris_object.Get.return_value = '...'
        self.mpris_frontend.track_playback_started(TlTrack())
        self.assertListEqual(self.mpris_object.Get.call_args_list, [
            ((objects.PLAYER_IFACE, 'PlaybackStatus'), {}),
            ((objects.PLAYER_IFACE, 'Metadata'), {}),
        ])
        self.mpris_object.PropertiesChanged.assert_called_with(
            objects.PLAYER_IFACE,
            {'Metadata': '...', 'PlaybackStatus': '...'}, [])

    def test_track_playback_ended_changes_playback_status_and_metadata(self):
        self.mpris_object.Get.return_value = '...'
        self.mpris_frontend.track_playback_ended(TlTrack(), 0)
        self.assertListEqual(self.mpris_object.Get.call_args_list, [
            ((objects.PLAYER_IFACE, 'PlaybackStatus'), {}),
            ((objects.PLAYER_IFACE, 'Metadata'), {}),
        ])
        self.mpris_object.PropertiesChanged.assert_called_with(
            objects.PLAYER_IFACE,
            {'Metadata': '...', 'PlaybackStatus': '...'}, [])

    def test_volume_changed_event_changes_volume(self):
        self.mpris_object.Get.return_value = 1.0
        self.mpris_frontend.volume_changed(volume=100)
        self.assertListEqual(self.mpris_object.Get.call_args_list, [
            ((objects.PLAYER_IFACE, 'Volume'), {}),
        ])
        self.mpris_object.PropertiesChanged.assert_called_with(
            objects.PLAYER_IFACE, {'Volume': 1.0}, [])

    def test_seeked_event_causes_mpris_seeked_event(self):
        self.mpris_frontend.seeked(31000)
        self.mpris_object.Seeked.assert_called_with(31000000)

    def test_playlists_loaded_event_changes_playlist_count(self):
        self.mpris_object.Get.return_value = 17
        self.mpris_frontend.playlists_loaded()
        self.assertListEqual(self.mpris_object.Get.call_args_list, [
            ((objects.PLAYLISTS_IFACE, 'PlaylistCount'), {}),
        ])
        self.mpris_object.PropertiesChanged.assert_called_with(
            objects.PLAYLISTS_IFACE, {'PlaylistCount': 17}, [])

    def test_playlist_changed_event_causes_mpris_playlist_changed_event(self):
        self.mpris_object.get_playlist_id.return_value = 'id-for-dummy:foo'
        playlist = Playlist(uri='dummy:foo', name='foo')
        self.mpris_frontend.playlist_changed(playlist)
        self.mpris_object.PlaylistChanged.assert_called_with(
            ('id-for-dummy:foo', 'foo', ''))
