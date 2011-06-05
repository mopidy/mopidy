import mock
import unittest

from pykka.registry import ActorRegistry

from mopidy.backends.base import Backend
from mopidy.backends.base.playback import PlaybackController
from mopidy.frontends import mpris

class PlayerInterfaceTest(unittest.TestCase):
    def setUp(self):
        mpris.ActorRegistry = mock.Mock(spec=ActorRegistry)
        mpris.MprisObject._connect_to_dbus = mock.Mock()
        self.backend = mock.Mock(spec=Backend)
        self.mpris_object = mpris.MprisObject()
        self.mpris_object._backend = self.backend

    def test_playback_status_is_playing_when_playing(self):
        self.backend.playback.state.get.return_value = PlaybackController.PLAYING
        result = self.mpris_object.Get(mpris.PLAYER_IFACE, 'PlaybackStatus')
        self.assertEqual('Playing', result)

    def test_playback_status_is_paused_when_paused(self):
        self.backend.playback.state.get.return_value = PlaybackController.PAUSED
        result = self.mpris_object.Get(mpris.PLAYER_IFACE, 'PlaybackStatus')
        self.assertEqual('Paused', result)

    def test_playback_status_is_stopped_when_stopped(self):
        self.backend.playback.state.get.return_value = PlaybackController.STOPPED
        result = self.mpris_object.Get(mpris.PLAYER_IFACE, 'PlaybackStatus')
        self.assertEqual('Stopped', result)

    def test_next_should_call_next_on_backend(self):
        self.mpris_object.Next()
        self.assert_(self.backend.playback.next.called)

    def test_pause_should_call_pause_on_backend(self):
        self.mpris_object.Pause()
        self.assert_(self.backend.playback.pause.called)

    def test_previous_should_call_previous_on_backend(self):
        self.mpris_object.Previous()
        self.assert_(self.backend.playback.previous.called)

    def test_stop_should_call_stop_on_backend(self):
        self.mpris_object.Stop()
        self.assert_(self.backend.playback.stop.called)
