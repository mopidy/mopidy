import mock
import unittest

from mopidy.frontends.mpris import MprisFrontend, MprisObject, PLAYER_IFACE
from mopidy.models import Track

class BackendEventsTest(unittest.TestCase):
    def setUp(self):
        self.mpris_frontend = MprisFrontend() # As a plain class, not an actor
        self.mpris_object = mock.Mock(spec=MprisObject)
        self.mpris_frontend.mpris_object = self.mpris_object

    def test_paused_playing_event_changes_playback_status(self):
        self.mpris_object.Get.return_value = 'Paused'
        self.mpris_frontend.paused_playing(Track(), 0)
        self.mpris_object.Get.assert_called_with(
            PLAYER_IFACE, 'PlaybackStatus')
        self.mpris_object.PropertiesChanged.assert_called_with(
            PLAYER_IFACE, {'PlaybackStatus': 'Paused'}, [])

    def test_resumed_playing_event_changes_playback_status(self):
        self.mpris_object.Get.return_value = 'Playing'
        self.mpris_frontend.resumed_playing(Track(), 0)
        self.mpris_object.Get.assert_called_with(
            PLAYER_IFACE, 'PlaybackStatus')
        self.mpris_object.PropertiesChanged.assert_called_with(
            PLAYER_IFACE, {'PlaybackStatus': 'Playing'}, [])

    def test_started_playing_event_changes_playback_status(self):
        self.mpris_object.Get.return_value = 'Playing'
        self.mpris_frontend.started_playing(Track())
        self.mpris_object.Get.assert_called_with(
            PLAYER_IFACE, 'PlaybackStatus')
        self.mpris_object.PropertiesChanged.assert_called_with(
            PLAYER_IFACE, {'PlaybackStatus': 'Playing'}, [])

    def test_stopped_playing_event_changes_playback_status(self):
        self.mpris_object.Get.return_value = 'Stopped'
        self.mpris_frontend.stopped_playing(Track(), 0)
        self.mpris_object.Get.assert_called_with(
            PLAYER_IFACE, 'PlaybackStatus')
        self.mpris_object.PropertiesChanged.assert_called_with(
            PLAYER_IFACE, {'PlaybackStatus': 'Stopped'}, [])
