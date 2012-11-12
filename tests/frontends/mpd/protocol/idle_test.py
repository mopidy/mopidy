from __future__ import unicode_literals

from mock import patch

from mopidy.frontends.mpd.protocol.status import SUBSYSTEMS

from tests.frontends.mpd import protocol


class IdleHandlerTest(protocol.BaseTestCase):
    def idleEvent(self, subsystem):
        self.session.on_idle(subsystem)

    def assertEqualEvents(self, events):
        self.assertEqual(set(events), self.context.events)

    def assertEqualSubscriptions(self, events):
        self.assertEqual(set(events), self.context.subscriptions)

    def assertNoEvents(self):
        self.assertEqualEvents([])

    def assertNoSubscriptions(self):
        self.assertEqualSubscriptions([])

    def test_base_state(self):
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertNoResponse()

    def test_idle(self):
        self.sendRequest('idle')
        self.assertEqualSubscriptions(SUBSYSTEMS)
        self.assertNoEvents()
        self.assertNoResponse()

    def test_idle_disables_timeout(self):
        self.sendRequest('idle')
        self.connection.disable_timeout.assert_called_once_with()

    def test_noidle(self):
        self.sendRequest('noidle')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertNoResponse()

    def test_idle_player(self):
        self.sendRequest('idle player')
        self.assertEqualSubscriptions(['player'])
        self.assertNoEvents()
        self.assertNoResponse()

    def test_idle_player_playlist(self):
        self.sendRequest('idle player playlist')
        self.assertEqualSubscriptions(['player', 'playlist'])
        self.assertNoEvents()
        self.assertNoResponse()

    def test_idle_then_noidle(self):
        self.sendRequest('idle')
        self.sendRequest('noidle')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertOnceInResponse('OK')

    def test_idle_then_noidle_enables_timeout(self):
        self.sendRequest('idle')
        self.sendRequest('noidle')
        self.connection.enable_timeout.assert_called_once_with()

    def test_idle_then_play(self):
        with patch.object(self.session, 'stop') as stop_mock:
            self.sendRequest('idle')
            self.sendRequest('play')
            stop_mock.assert_called_once_with()

    def test_idle_then_idle(self):
        with patch.object(self.session, 'stop') as stop_mock:
            self.sendRequest('idle')
            self.sendRequest('idle')
            stop_mock.assert_called_once_with()

    def test_idle_player_then_play(self):
        with patch.object(self.session, 'stop') as stop_mock:
            self.sendRequest('idle player')
            self.sendRequest('play')
            stop_mock.assert_called_once_with()

    def test_idle_then_player(self):
        self.sendRequest('idle')
        self.idleEvent('player')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertOnceInResponse('changed: player')
        self.assertOnceInResponse('OK')

    def test_idle_player_then_event_player(self):
        self.sendRequest('idle player')
        self.idleEvent('player')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertOnceInResponse('changed: player')
        self.assertOnceInResponse('OK')

    def test_idle_player_then_noidle(self):
        self.sendRequest('idle player')
        self.sendRequest('noidle')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertOnceInResponse('OK')

    def test_idle_player_playlist_then_noidle(self):
        self.sendRequest('idle player playlist')
        self.sendRequest('noidle')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse('OK')

    def test_idle_player_playlist_then_player(self):
        self.sendRequest('idle player playlist')
        self.idleEvent('player')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse('changed: player')
        self.assertNotInResponse('changed: playlist')
        self.assertOnceInResponse('OK')

    def test_idle_playlist_then_player(self):
        self.sendRequest('idle playlist')
        self.idleEvent('player')
        self.assertEqualEvents(['player'])
        self.assertEqualSubscriptions(['playlist'])
        self.assertNoResponse()

    def test_idle_playlist_then_player_then_playlist(self):
        self.sendRequest('idle playlist')
        self.idleEvent('player')
        self.idleEvent('playlist')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertNotInResponse('changed: player')
        self.assertOnceInResponse('changed: playlist')
        self.assertOnceInResponse('OK')

    def test_player(self):
        self.idleEvent('player')
        self.assertEqualEvents(['player'])
        self.assertNoSubscriptions()
        self.assertNoResponse()

    def test_player_then_idle_player(self):
        self.idleEvent('player')
        self.sendRequest('idle player')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse('changed: player')
        self.assertNotInResponse('changed: playlist')
        self.assertOnceInResponse('OK')

    def test_player_then_playlist(self):
        self.idleEvent('player')
        self.idleEvent('playlist')
        self.assertEqualEvents(['player', 'playlist'])
        self.assertNoSubscriptions()
        self.assertNoResponse()

    def test_player_then_idle(self):
        self.idleEvent('player')
        self.sendRequest('idle')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse('changed: player')
        self.assertOnceInResponse('OK')

    def test_player_then_playlist_then_idle(self):
        self.idleEvent('player')
        self.idleEvent('playlist')
        self.sendRequest('idle')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse('changed: player')
        self.assertOnceInResponse('changed: playlist')
        self.assertOnceInResponse('OK')

    def test_player_then_idle_playlist(self):
        self.idleEvent('player')
        self.sendRequest('idle playlist')
        self.assertEqualEvents(['player'])
        self.assertEqualSubscriptions(['playlist'])
        self.assertNoResponse()

    def test_player_then_idle_playlist_then_noidle(self):
        self.idleEvent('player')
        self.sendRequest('idle playlist')
        self.sendRequest('noidle')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse('OK')

    def test_player_then_playlist_then_idle_playlist(self):
        self.idleEvent('player')
        self.idleEvent('playlist')
        self.sendRequest('idle playlist')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertNotInResponse('changed: player')
        self.assertOnceInResponse('changed: playlist')
        self.assertOnceInResponse('OK')
