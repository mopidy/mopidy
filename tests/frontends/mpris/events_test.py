import mock
import unittest

from mopidy.frontends.mpris import MprisFrontend, MprisObject, PLAYER_IFACE
from mopidy.models import Track

class BackendEventsTest(unittest.TestCase):
    def setUp(self):
        self.mpris_frontend = MprisFrontend() # As a plain class, not an actor
        self.mpris_object = mock.Mock(spec=MprisObject)
        self.mpris_frontend.mpris_object = self.mpris_object

    def test_track_playback_paused_event_changes_playback_status(self):
        self.mpris_object.Get.return_value = 'Paused'
        self.mpris_frontend.track_playback_paused(Track(), 0)
        self.assertListEqual(self.mpris_object.Get.call_args_list, [
            ((PLAYER_IFACE, 'PlaybackStatus'), {}),
        ])
        self.mpris_object.PropertiesChanged.assert_called_with(
            PLAYER_IFACE, {'PlaybackStatus': 'Paused'}, [])

    def test_track_playback_resumed_event_changes_playback_status(self):
        self.mpris_object.Get.return_value = 'Playing'
        self.mpris_frontend.track_playback_resumed(Track(), 0)
        self.assertListEqual(self.mpris_object.Get.call_args_list, [
            ((PLAYER_IFACE, 'PlaybackStatus'), {}),
        ])
        self.mpris_object.PropertiesChanged.assert_called_with(
            PLAYER_IFACE, {'PlaybackStatus': 'Playing'}, [])

    def test_track_playback_started_event_changes_playback_status_and_metadata(self):
        self.mpris_object.Get.return_value = '...'
        self.mpris_frontend.track_playback_started(Track())
        self.assertListEqual(self.mpris_object.Get.call_args_list, [
            ((PLAYER_IFACE, 'Metadata'), {}),
            ((PLAYER_IFACE, 'PlaybackStatus'), {}),
        ])
        self.mpris_object.PropertiesChanged.assert_called_with(
            PLAYER_IFACE, {'Metadata': '...', 'PlaybackStatus': '...'}, [])

    def test_track_playback_ended_event_changes_playback_status_and_metadata(self):
        self.mpris_object.Get.return_value = '...'
        self.mpris_frontend.track_playback_ended(Track(), 0)
        self.assertListEqual(self.mpris_object.Get.call_args_list, [
            ((PLAYER_IFACE, 'Metadata'), {}),
            ((PLAYER_IFACE, 'PlaybackStatus'), {}),
        ])
        self.mpris_object.PropertiesChanged.assert_called_with(
            PLAYER_IFACE, {'Metadata': '...', 'PlaybackStatus': '...'}, [])
