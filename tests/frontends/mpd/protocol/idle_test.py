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
        self.sendRequest(u'idle')
        self.assertEqualSubscriptions(SUBSYSTEMS)
        self.assertNoEvents()
        self.assertNoResponse()

    def test_idle_disables_timeout(self):
        self.sendRequest(u'idle')
        self.connection.disable_timeout.assert_called_once_with()

    def test_noidle(self):
        self.sendRequest(u'noidle')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertNoResponse()

    def test_idle_player(self):
        self.sendRequest(u'idle player')
        self.assertEqualSubscriptions(['player'])
        self.assertNoEvents()
        self.assertNoResponse()

    def test_idle_player_playlist(self):
        self.sendRequest(u'idle player playlist')
        self.assertEqualSubscriptions(['player', 'playlist'])
        self.assertNoEvents()
        self.assertNoResponse()

    def test_idle_then_noidle(self):
        self.sendRequest(u'idle')
        self.sendRequest(u'noidle')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertOnceInResponse(u'OK')

    def test_idle_then_noidle_enables_timeout(self):
        self.sendRequest(u'idle')
        self.sendRequest(u'noidle')
        self.connection.enable_timeout.assert_called_once_with()

    def test_idle_then_play(self):
        with patch.object(self.session, 'stop') as stop_mock:
            self.sendRequest(u'idle')
            self.sendRequest(u'play')
            stop_mock.assert_called_once_with()

    def test_idle_then_idle(self):
        with patch.object(self.session, 'stop') as stop_mock:
            self.sendRequest(u'idle')
            self.sendRequest(u'idle')
            stop_mock.assert_called_once_with()

    def test_idle_player_then_play(self):
        with patch.object(self.session, 'stop') as stop_mock:
            self.sendRequest(u'idle player')
            self.sendRequest(u'play')
            stop_mock.assert_called_once_with()

    def test_idle_then_player(self):
        self.sendRequest(u'idle')
        self.idleEvent(u'player')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertOnceInResponse(u'changed: player')
        self.assertOnceInResponse(u'OK')

    def test_idle_player_then_event_player(self):
        self.sendRequest(u'idle player')
        self.idleEvent(u'player')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertOnceInResponse(u'changed: player')
        self.assertOnceInResponse(u'OK')

    def test_idle_player_then_noidle(self):
        self.sendRequest(u'idle player')
        self.sendRequest(u'noidle')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertOnceInResponse(u'OK')

    def test_idle_player_playlist_then_noidle(self):
        self.sendRequest(u'idle player playlist')
        self.sendRequest(u'noidle')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse(u'OK')

    def test_idle_player_playlist_then_player(self):
        self.sendRequest(u'idle player playlist')
        self.idleEvent(u'player')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse(u'changed: player')
        self.assertNotInResponse(u'changed: playlist')
        self.assertOnceInResponse(u'OK')

    def test_idle_playlist_then_player(self):
        self.sendRequest(u'idle playlist')
        self.idleEvent(u'player')
        self.assertEqualEvents(['player'])
        self.assertEqualSubscriptions(['playlist'])
        self.assertNoResponse()

    def test_idle_playlist_then_player_then_playlist(self):
        self.sendRequest(u'idle playlist')
        self.idleEvent(u'player')
        self.idleEvent(u'playlist')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertNotInResponse(u'changed: player')
        self.assertOnceInResponse(u'changed: playlist')
        self.assertOnceInResponse(u'OK')

    def test_player(self):
        self.idleEvent(u'player')
        self.assertEqualEvents(['player'])
        self.assertNoSubscriptions()
        self.assertNoResponse()

    def test_player_then_idle_player(self):
        self.idleEvent(u'player')
        self.sendRequest(u'idle player')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse(u'changed: player')
        self.assertNotInResponse(u'changed: playlist')
        self.assertOnceInResponse(u'OK')

    def test_player_then_playlist(self):
        self.idleEvent(u'player')
        self.idleEvent(u'playlist')
        self.assertEqualEvents(['player', 'playlist'])
        self.assertNoSubscriptions()
        self.assertNoResponse()

    def test_player_then_idle(self):
        self.idleEvent(u'player')
        self.sendRequest(u'idle')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse(u'changed: player')
        self.assertOnceInResponse(u'OK')

    def test_player_then_playlist_then_idle(self):
        self.idleEvent(u'player')
        self.idleEvent(u'playlist')
        self.sendRequest(u'idle')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse(u'changed: player')
        self.assertOnceInResponse(u'changed: playlist')
        self.assertOnceInResponse(u'OK')

    def test_player_then_idle_playlist(self):
        self.idleEvent(u'player')
        self.sendRequest(u'idle playlist')
        self.assertEqualEvents(['player'])
        self.assertEqualSubscriptions(['playlist'])
        self.assertNoResponse()

    def test_player_then_idle_playlist_then_noidle(self):
        self.idleEvent(u'player')
        self.sendRequest(u'idle playlist')
        self.sendRequest(u'noidle')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse(u'OK')

    def test_player_then_playlist_then_idle_playlist(self):
        self.idleEvent(u'player')
        self.idleEvent(u'playlist')
        self.sendRequest(u'idle playlist')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertNotInResponse(u'changed: player')
        self.assertOnceInResponse(u'changed: playlist')
        self.assertOnceInResponse(u'OK')
