import sys

import mock

from mopidy import OptionalDependencyError
from mopidy.models import Track

try:
    from mopidy.frontends.mpris import MprisFrontend, objects
except OptionalDependencyError:
    pass

from tests import unittest


@unittest.skipUnless(sys.platform.startswith('linux'), 'requires Linux')
class BackendEventsTest(unittest.TestCase):
    def setUp(self):
        self.mpris_frontend = MprisFrontend() # As a plain class, not an actor
        self.mpris_object = mock.Mock(spec=objects.MprisObject)
        self.mpris_frontend.mpris_object = self.mpris_object

    def test_track_playback_paused_event_changes_playback_status(self):
        self.mpris_object.Get.return_value = 'Paused'
        self.mpris_frontend.track_playback_paused(Track(), 0)
        self.assertListEqual(self.mpris_object.Get.call_args_list, [
            ((objects.PLAYER_IFACE, 'PlaybackStatus'), {}),
        ])
        self.mpris_object.PropertiesChanged.assert_called_with(
            objects.PLAYER_IFACE, {'PlaybackStatus': 'Paused'}, [])

    def test_track_playback_resumed_event_changes_playback_status(self):
        self.mpris_object.Get.return_value = 'Playing'
        self.mpris_frontend.track_playback_resumed(Track(), 0)
        self.assertListEqual(self.mpris_object.Get.call_args_list, [
            ((objects.PLAYER_IFACE, 'PlaybackStatus'), {}),
        ])
        self.mpris_object.PropertiesChanged.assert_called_with(
            objects.PLAYER_IFACE, {'PlaybackStatus': 'Playing'}, [])

    def test_track_playback_started_event_changes_playback_status_and_metadata(self):
        self.mpris_object.Get.return_value = '...'
        self.mpris_frontend.track_playback_started(Track())
        self.assertListEqual(self.mpris_object.Get.call_args_list, [
            ((objects.PLAYER_IFACE, 'PlaybackStatus'), {}),
            ((objects.PLAYER_IFACE, 'Metadata'), {}),
        ])
        self.mpris_object.PropertiesChanged.assert_called_with(
            objects.PLAYER_IFACE,
            {'Metadata': '...', 'PlaybackStatus': '...'}, [])

    def test_track_playback_ended_event_changes_playback_status_and_metadata(self):
        self.mpris_object.Get.return_value = '...'
        self.mpris_frontend.track_playback_ended(Track(), 0)
        self.assertListEqual(self.mpris_object.Get.call_args_list, [
            ((objects.PLAYER_IFACE, 'PlaybackStatus'), {}),
            ((objects.PLAYER_IFACE, 'Metadata'), {}),
        ])
        self.mpris_object.PropertiesChanged.assert_called_with(
            objects.PLAYER_IFACE,
            {'Metadata': '...', 'PlaybackStatus': '...'}, [])

    def test_volume_changed_event_changes_volume(self):
        self.mpris_object.Get.return_value = 1.0
        self.mpris_frontend.volume_changed()
        self.assertListEqual(self.mpris_object.Get.call_args_list, [
            ((objects.PLAYER_IFACE, 'Volume'), {}),
        ])
        self.mpris_object.PropertiesChanged.assert_called_with(
            objects.PLAYER_IFACE, {'Volume': 1.0}, [])

    def test_seeked_event_causes_mpris_seeked_event(self):
        self.mpris_object.Get.return_value = 31000000
        self.mpris_frontend.seeked()
        self.assertListEqual(self.mpris_object.Get.call_args_list, [
            ((objects.PLAYER_IFACE, 'Position'), {}),
        ])
        self.mpris_object.Seeked.assert_called_with(31000000)
